"""Audit V1 frontend evidence without executing any dataset command or changing V1.

Builds a quarantine/replay ledger, not an approved training corpus. Synthetic tool
output is never upgraded to execution evidence. --check verifies committed output.
Optional TypeScript diagnostics come from check_frontend_snapshots.cjs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

try:
    from .to_pi_format import convert
except ImportError:
    from to_pi_format import convert

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "datasets/frontend-stack"
OUT = FRONTEND / "v2/review/hardening"
BATCHES = {
    "batch1": "batch1_forms_bugfix_medium.jsonl",
    "batch2": "batch2_mixed_25.jsonl",
    "batch3": "batch3_mixed_100.jsonl",
    "batch4": "batch4_mixed_100.jsonl",
    "batch5": "batch5_mixed_100.jsonl",
}
FAILURE = re.compile(r"(?im)^\s*(?:Error:|error:|ENOENT\b|EACCES\b|FAIL(?:\s|$)|[^\n]*error TS\d+|(?:Test Files|Tests)\s+[1-9]\d*\s+failed\b|(?:sh|bash|zsh):[^\n]*command not found|npm ERR!)")
VERIFY = re.compile(r"\b(?:tsc|vitest|jest|playwright|eslint)\b|\bvite\s+build\b|\b(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?(?:test|build|lint|typecheck|check)\b")
CLAIM = re.compile(r"\b(?:pass(?:es|ed|ing)?|verified|confirmed|green|clean|typechecks?)\b", re.I)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def words(text):
    return re.findall(r"[a-z0-9_]+", text.lower())


def prompt(row):
    return "\n".join(m.get("content", "") for m in row["messages"] if m.get("role") == "user")


def closed_schema(schema):
    schema = copy.deepcopy(schema)
    if schema.get("type") == "object" and "properties" in schema:
        schema["additionalProperties"] = False
        schema["properties"] = {k: closed_schema(v) for k, v in schema["properties"].items()}
    if "items" in schema:
        schema["items"] = closed_schema(schema["items"])
    return schema


def tool_contract_errors(messages, tools):
    """Validate contiguous results, declared names, argument types and unknown keys."""
    validators = {t["function"]["name"]: Draft202012Validator(closed_schema(t["function"]["parameters"])) for t in tools}
    errors = []
    if not messages or messages[-1].get("role") != "assistant" or messages[-1].get("tool_calls") or not messages[-1].get("content", "").strip():
        errors.append("final message must be a nonempty assistant summary")
    i = 0
    while i < len(messages):
        m = messages[i]
        if m.get("role") not in {"system", "user", "assistant", "tool"}:
            errors.append(f"message {i}: invalid role")
        if m.get("role") == "tool":
            errors.append(f"message {i}: orphan result")
        if m.get("role") != "assistant" and "tool_calls" in m:
            errors.append(f"message {i}: calls on non-assistant")
        calls = m.get("tool_calls")
        if calls is None:
            i += 1
            continue
        if not isinstance(calls, list) or not calls:
            errors.append(f"message {i}: empty/invalid calls")
            i += 1
            continue
        results = messages[i + 1:i + 1 + len(calls)]
        for n, call in enumerate(calls):
            name = call.get("name")
            if name not in validators:
                errors.append(f"message {i}: undeclared tool {name}")
            else:
                errors.extend(f"message {i} {name}: {e.message}" for e in validators[name].iter_errors(call.get("arguments")))
            if n >= len(results) or results[n].get("role") != "tool" or results[n].get("name") not in {None, "", name}:
                errors.append(f"message {i}: missing/mismatched result for {name}")
        i += len(calls) + 1
    return errors


def apply_edits(content, edits):
    """Match unique, non-overlapping edits against the ORIGINAL snapshot."""
    spans = []
    for edit in edits:
        old, new = edit["oldText"], edit["newText"]
        if not old:
            raise ValueError("empty edit target")
        count = content.count(old)
        if count != 1:
            raise ValueError(f"edit target occurs {count} times")
        start = content.index(old)
        spans.append((start, start + len(old), new))
    spans.sort()
    if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
        raise ValueError("overlapping edits")
    for start, end, new in reversed(spans):
        content = content[:start] + new + content[end:]
    return content


def audit_trace(row, tools):
    findings, snapshots, partial, commands = [], {}, set(), []
    observed = {}
    modified = set()
    last_edit = -1

    def add(code, severity, message, detail):
        findings.append({"code": code, "severity": severity, "message": message, "detail": detail})

    for error in tool_contract_errors(row["messages"], tools):
        add("tool_contract", "defect", None, error)
    if findings:
        return findings, {}, [], set()
    for i, m in enumerate(row["messages"]):
        for n, call in enumerate(m.get("tool_calls", [])):
            result = row["messages"][i + n + 1]
            output = result.get("content", "")
            name, args = call["name"], call["arguments"]
            path = args.get("path", "").replace("\\", "/")
            failed = bool(FAILURE.search(output)) if name == "bash" else bool(re.match(r"\s*(?:Error:|error:|ENOENT\b|EACCES\b|Cannot read\b|Could not find\b|File not found\b)", output))
            if name in {"grep", "bash"}:
                for line in output.splitlines():
                    match = re.match(r"^((?:[A-Za-z]:[/\\])?[^:\n]+\.[a-z]+)(?::(?:\d+:)?|-\d+-)(.*)$", line)
                    if match:
                        observed.setdefault(match[1].replace("\\", "/"), []).append(match[2])
            if name == "bash":
                command = args["command"]
                commands.append({"message": i, "command": command, "recorded_failure": failed, "is_check": bool(VERIFY.search(command)), "output": output})
            elif name == "read" and not failed:
                if output.strip() == "(file is empty - 0 bytes)":
                    output = ""
                clipped = args.get("offset", 1) > 1 or "limit" in args or bool(re.search(r"(?im)(?:returned the first|No content returned|^\s*[\[(](?:read_file |file |output )?truncated\b|^.* lines \d+-\d+:|^// lines \d+)", output))
                if clipped:
                    partial.add(path)
                elif path in snapshots and path not in partial and snapshots[path] != output:
                    add("read_state_drift", "review", i, path)
                snapshots[path] = output
            elif name == "write" and not failed:
                if path not in snapshots and (path in observed or any(path in c["command"] for c in commands)):
                    add("overwrite_without_read", "review", i, path + ": existing-file evidence precedes an unread overwrite")
                snapshots[path] = args["content"]
                partial.discard(path)
                modified.add(path)
                last_edit = i
            elif name == "edit" and not failed:
                modified.add(path)
                last_edit = i
                if path not in snapshots:
                    context = "\n".join(observed.get(path, []))
                    # Compiler diagnostics can also expose exact edit context. This
                    # remains partial evidence, never a full reconstructed source file.
                    for command in commands:
                        if path in command["output"]:
                            context += "\n" + re.sub(r"(?m)^\s*\d+[| ]", "", command["output"])
                    if all(e["oldText"] in context for e in args["edits"]):
                        add("edit_from_search_fragment", "review", i, path + ": context observed in search/diagnostics; full-file uniqueness unverified")
                    else:
                        add("edit_without_read", "defect", i, path)
                    continue
                try:
                    snapshots[path] = apply_edits(snapshots[path], args["edits"])
                except ValueError as exc:
                    add("edit_context_mismatch", "review" if path in partial else "defect", i, f"{path}: {exc}")
    checks = [c for c in commands if c["is_check"]]
    after = [c for c in checks if c["message"] > last_edit]
    if not checks:
        add("no_verification_command", "defect", None, "No recorded test, typecheck, build or lint command")
    elif not after:
        add("verification_before_last_edit", "defect", None, "No check after final successful recorded edit")
    elif all(c["recorded_failure"] for c in after):
        add("unresolved_verification_failure", "review", after[-1]["message"], after[-1]["command"] + ": inspect whether failure is acknowledged and predates changes")
    summary = row["messages"][-1].get("content", "")
    if CLAIM.search(summary) and not any(not c["recorded_failure"] for c in after):
        add("summary_failure_scope_review", "review", len(row["messages"]) - 1, summary)
    if re.search(r"\b(?:browser|visually|screenshot|clicked|dragged)\b", summary, re.I):
        add("visual_claim_review", "review", len(row["messages"]) - 1, summary)
    if re.search(r"unmount(?:ed)?.{0,100}warn|warn.{0,100}unmount", summary, re.I | re.S):
        add("react_version_claim_review", "review", len(row["messages"]) - 1, "Verify React version and distinguish obsolete unmounted-state warnings from actual leaks or races")
    if partial:
        add("partial_file_context", "review", None, ", ".join(sorted(partial)))
    # Never infer genuine execution from blank stdout or synthetically authored metadata.
    add("synthetic_execution_unverified", "provenance", None, "V1 authoring requested realistic tool results; no captured run evidence or immutable source identity")
    return findings, {p: text for p, text in snapshots.items() if p not in partial}, commands, modified


def coverage(text):
    patterns = {
        "state_async_lifecycle": r"useEffect|useReducer|useCallback|AbortController|race|stale|cleanup",
        "forms_validation": r"form|validat|submit|field|input",
        "accessibility_keyboard": r"aria-|keyboard|focus|tabindex|screen reader",
        "layout_responsive": r"overflow|responsive|grid|flex|viewport|scroll|resize",
        "data_persistence": r"fetch|storage|persist|request|cache|pagination",
        "routing": r"router|route|navigate|history",
        "test_authoring": r"(?:\.test\.|\.spec\.)",
    }
    return [tag for tag, expression in patterns.items() if re.search(expression, text, re.I)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--diagnostics", type=Path, default=OUT / "typescript-diagnostics.json", help="Static TypeScript report; must match reconstructed snapshots")
    parser.add_argument("--snapshots", type=Path, help="Write inert reconstructed snapshots for static checking")
    args = parser.parse_args()
    tools = json.loads((ROOT / "training/pi_tools.json").read_text(encoding="utf-8"))
    keep = read_jsonl(FRONTEND / "filtered/keep_ge7.jsonl")
    pi_keep = read_jsonl(FRONTEND / "filtered/keep_ge7.pi.jsonl")
    index = json.loads((FRONTEND / "filtered/keep_ge7.index.json").read_text())
    assert len(keep) == len(pi_keep) == len(index)
    keep_by_id = {f"{item['batch']}:{item['line']}": (n, item["score"]) for n, item in enumerate(index, 1)}
    records, inputs = {}, []
    for batch, filename in BATCHES.items():
        path = FRONTEND / "generated/raw" / filename
        inputs.append(path)
        for n, row in enumerate(read_jsonl(path), 1):
            records[f"{batch}:{n}"] = row
    for n, row in enumerate(read_jsonl(FRONTEND / "seeds/seeds.jsonl"), 1):
        records[f"seed:{n}"] = {"messages": row["messages"]}
    for n, (row, converted, ref) in enumerate(zip(keep, pi_keep, index), 1):
        assert row == records[f"{ref['batch']}:{ref['line']}"], f"keep/raw drift at {n}"
        expected = convert(copy.deepcopy(row))
        # V1 final mix adds find/ls to the system prompt; pi keep is exact converter output.
        assert expected == converted, f"pi conversion drift at {n}"
    eval_prompts = []
    for path in sorted((ROOT / "evals/tasks").rglob("*.md")):
        match = re.search(r"## Prompt[^\n]*\n(.*?)\n## Success criteria", path.read_text(encoding="utf-8"), re.S)
        if match:
            eval_prompts.append((path.relative_to(ROOT).as_posix(), set(words(match[1]))))
    diagnostics = json.loads(args.diagnostics.read_text(encoding="utf-8")) if args.diagnostics.is_file() and not args.snapshots else {"records": {}}
    decisions_path = OUT / "semantic-decisions.json"
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))["records"]
    ledger, snapshot_rows, replay_candidates = [], [], []
    for record_id, raw in records.items():
        try:
            row = convert(copy.deepcopy(raw))
            findings, snapshots, commands, modified = audit_trace(row, tools)
        except (KeyError, ValueError, TypeError, IndexError) as exc:
            findings = [{"code": "conversion_failure", "severity": "defect", "message": None, "detail": str(exc)}]
            snapshots, commands, modified = {}, [], set()
        text = canonical(raw)
        pwords = set(words(prompt(raw)))
        overlaps = []
        for path, ewords in eval_prompts:
            similarity = len(pwords & ewords) / max(1, len(pwords | ewords))
            if len(pwords & ewords) >= 12 and similarity >= .45:
                overlaps.append({"eval": path, "jaccard": round(similarity, 3)})
        if overlaps:
            findings.append({"code": "eval_prompt_similarity", "severity": "review", "message": None, "detail": overlaps})
        static = diagnostics["records"].get(record_id, [])
        for issue in static:
            ambient = issue["code"] in {2304, 2552} and bool(re.search(r"'(?:expect|describe|it|test|beforeEach|afterEach|vi|jest|global|process|__dirname|require|Buffer)'", issue["text"]))
            findings.append({"code": "typescript_environment_dependency" if ambient else "typescript_static_error", "severity": "review" if ambient else "defect", "message": None, "detail": issue})
        retained = keep_by_id.get(record_id)
        semantic = decisions.get(record_id)
        if semantic:
            if semantic.get("source_sha256") != digest(raw):
                raise SystemExit(f"semantic decision source drift: {record_id}")
            findings.append({"code": "semantic_" + semantic["action"], "severity": "defect" if semantic["action"] == "quarantine" else "review", "message": None, "detail": semantic["reason"]})
        if retained and not any(f["severity"] == "defect" for f in findings):
            candidate = copy.deepcopy(row)
            if semantic and semantic["action"] == "repair_summary":
                candidate["messages"][-1]["content"] = semantic["replacement_summary"]
            replay_candidates.append({"id": record_id, "status": "synthetic_replay_candidate", "training_eligible": False, "source_sha256": digest(raw), "messages": candidate["messages"], "tools": tools})
        entry = {
            "id": record_id, "source_sha256": digest(raw),
            "v1_keep_line": retained[0] if retained else None,
            "v1_score": retained[1] if retained else None,
            "decision": "quarantine" if any(f["severity"] == "defect" for f in findings) else "replay_required",
            "training_eligible": False, "findings": findings,
            "coverage_tags": coverage(text), "prompt": prompt(raw),
            "modified_paths": sorted(modified), "recorded_check_commands": [c["command"] for c in commands if c["is_check"]],
        }
        ledger.append(entry)
        snapshot_rows.append({"id": record_id, "files": snapshots})
    if args.snapshots:
        args.snapshots.parent.mkdir(parents=True, exist_ok=True)
        args.snapshots.write_text(canonical(snapshot_rows) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {len(snapshot_rows)} inert snapshot records; audit products unchanged")
        return
    if diagnostics.get("input_sha256") != hashlib.sha256((canonical(snapshot_rows) + "\n").encode()).hexdigest():
        raise SystemExit("TypeScript diagnostics missing or stale; regenerate snapshots and diagnostics first")
    if diagnostics.get("analyzer_sha256") != hashlib.sha256((ROOT / "scripts/check_frontend_snapshots.cjs").read_bytes()).hexdigest():
        raise SystemExit("TypeScript analyzer changed; regenerate diagnostics first")
    # Duplicated aggregates/parts are intentional copies, not independent examples.
    raw_files = sorted((FRONTEND / "generated/raw").glob("*.jsonl"))
    unique_raw = {digest(row) for row in records.values()}
    extra_raw = []
    for path in raw_files:
        inputs.append(path)
        for n, row in enumerate(read_jsonl(path), 1):
            if "messages" in row and digest(row) not in unique_raw:
                extra_raw.append(f"{path.name}:{n}")
    assert not extra_raw, f"unaccounted raw records: {extra_raw}"
    # Audit all final mixture records against their own declared tool contracts.
    mixes = {}
    for name in ("train", "holdout", "train-short4096", "holdout-short4096"):
        path = FRONTEND / "final" / f"{name}.jsonl"
        inputs.append(path)
        rows = read_jsonl(path)
        errors = []
        for n, row in enumerate(rows, 1):
            for error in tool_contract_errors(row["messages"], row.get("tools", [])):
                errors.append({"line": n, "error": error})
        mixes[name] = {"records": len(rows), "by_source": dict(Counter(r["source"] for r in rows)), "contract_errors": errors}
    train = read_jsonl(FRONTEND / "final/train.jsonl")
    holdout = read_jsonl(FRONTEND / "final/holdout.jsonl")
    # The mixer expands the system prompt, but must preserve every domain exchange.
    domain_identities = {digest(r["messages"][1:]) for r in pi_keep}
    mixed_domain = [r for r in train + holdout if r["source"] == "frontend-stack"]
    assert len(mixed_domain) == len(keep) and {digest(r["messages"][1:]) for r in mixed_domain} == domain_identities, "domain content drift in V1 final mix"
    for name, rows in (("train", train), ("holdout", holdout)):
        original = {digest(r) for r in rows}
        bounded = read_jsonl(FRONTEND / "final" / f"{name}-short4096.jsonl")
        assert all(digest(r) in original for r in bounded), f"bounded {name} contains a changed or cross-split record"
    split_overlap = sorted({" ".join(words(prompt(r))) for r in train} & {" ".join(words(prompt(r))) for r in holdout})
    general_quarantine, general_candidates = [], []
    for name, rows in (("train", train), ("holdout", holdout)):
        invalid_lines = {e["line"] for e in mixes[name]["contract_errors"]}
        for n, row in enumerate(rows, 1):
            if row["source"] != "frontend-stack" and n not in invalid_lines:
                general_candidates.append({"original_split": name, "original_line": n, "status": "schema_checked_not_training_release", "record": row})
        for n in sorted(invalid_lines):
            row = rows[n - 1]
            general_quarantine.append({"split": name, "line": n, "source": row["source"], "sha256": digest(row), "decision": "quarantine", "errors": [e["error"] for e in mixes[name]["contract_errors"] if e["line"] == n]})
    similarities = []
    for i, left in enumerate(keep):
        left_words = set(words(prompt(left)))
        for j in range(i + 1, len(keep)):
            right_words = set(words(prompt(keep[j])))
            score = len(left_words & right_words) / max(1, len(left_words | right_words))
            if score >= .5 and len(left_words & right_words) >= 12:
                similarities.append({"keep_lines": [i + 1, j + 1], "jaccard": round(score, 3), "decision": "review_before_split"})
    retained = [e for e in ledger if e["v1_keep_line"]]
    inputs += [FRONTEND / "filtered" / n for n in ("keep_ge7.jsonl", "keep_ge7.pi.jsonl", "keep_ge7.index.json")]
    inputs += [FRONTEND / "seeds/seeds.jsonl", ROOT / "training/pi_tools.json", decisions_path, args.diagnostics]
    manifest = {
        "schema_version": 1, "scope": "350 canonical raw trajectories, 2 seeds, all 242 retained, all V1 final splits; raw part copies reconciled",
        "training_ready": False, "execution_policy": "Never execute dataset commands; no synthetic output is accepted as captured execution",
        "raw_and_seed_records": len(ledger), "retained_records": len(retained),
        "all_decisions": dict(Counter(e["decision"] for e in ledger)),
        "retained_decisions": dict(Counter(e["decision"] for e in retained)),
        "retained_finding_counts": dict(sorted(Counter(f["code"] for e in retained for f in {x["code"]: x for x in e["findings"]}.values()).items())),
        "retained_coverage_tags": dict(sorted(Counter(tag for e in retained for tag in e["coverage_tags"]).items())),
        "coverage_method": "Overlapping lexical tags; not evidence of skill mastery or test adequacy",
        "eval_prompts_scanned": len(eval_prompts), "eval_similarity_method": "Token Jaccard >= .45 with >=12 shared tokens; heuristic only, not semantic/patch clearance",
        "train_holdout_normalized_prompt_overlap": split_overlap,
        "final_mixes": mixes,
        "general_quarantined_records": len(general_quarantine),
        "general_schema_checked_candidates": len(general_candidates),
        "retained_prompt_similarity_pairs": len(similarities),
        "retained_exact_prompt_duplicates": len(keep) - len({" ".join(words(prompt(r))) for r in keep}),
        "retained_exact_trace_duplicates": len(keep) - len({digest(r) for r in keep}),
        "v1_lineage_checks": "Raw/keep/pi conversion agree; all final domain exchanges match pi keep; bounded splits are unchanged subsets of their own source split",
        "typescript": {k: v for k, v in diagnostics.items() if k != "records"},
        "inputs": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(inputs))},
    }
    products = {
        "audit.jsonl": "".join(canonical(e) + "\n" for e in ledger),
        "replay-queue.jsonl": "".join(canonical(e) + "\n" for e in retained if e["decision"] == "replay_required"),
        "quarantine.jsonl": "".join(canonical(e) + "\n" for e in retained if e["decision"] == "quarantine"),
        "replay-candidates.jsonl": "".join(canonical(e) + "\n" for e in replay_candidates),
        "general-quarantine.jsonl": "".join(canonical(e) + "\n" for e in general_quarantine),
        "general-candidates.jsonl": "".join(canonical(e) + "\n" for e in general_candidates),
        "similarity-review.jsonl": "".join(canonical(e) + "\n" for e in similarities),
    }
    manifest["output_sha256"] = {name: hashlib.sha256(content.encode()).hexdigest() for name, content in products.items()}
    products["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    for name, content in products.items():
        path = OUT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"stale audit output: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({k: manifest[k] for k in ("raw_and_seed_records", "retained_decisions", "retained_finding_counts", "train_holdout_normalized_prompt_overlap")}))


if __name__ == "__main__":
    main()
