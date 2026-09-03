"""Build deterministic human-review queues from V2 source inventories.

Outputs:
- Up to 40 unique eval candidates for each not-yet-frozen specialist, minimum 20.
- A 121-record frontend score-7 semantic re-audit queue.

This script intentionally does not create training trajectories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "datasets/v2-registry.json"
FRONTEND_INDEX = ROOT / "datasets/frontend-stack/filtered/keep_ge7.index.json"
FRONTEND_KEEP = ROOT / "datasets/frontend-stack/filtered/keep_ge7.jsonl"
QUEUE_ORDER = ("security-review", "backend-stack", "testing-qa", "code-review")
SCOPE = re.compile(r"^[a-z]+\(([^)]+)\):")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )


def update_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise SystemExit(f"missing or stale queue: {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def subject_scope(subject: str) -> str:
    match = SCOPE.match(subject.lower())
    if match:
        return match.group(1)
    return subject.lower().split(":", 1)[0][:40]


def choose_eval_candidates(
    candidates: list[dict[str, Any]],
    count: int,
    globally_used: set[str],
) -> list[dict[str, Any]]:
    """Prefer high scores while limiting repository/scope monoculture."""
    eligible = [
        row for row in candidates
        if row["commit"] not in globally_used
        and row["parent"] not in globally_used
        and len(row["changed_files"]) <= 20
    ]
    eligible.sort(key=lambda row: (-row["score"], row["repository"], row["commit"]))
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        by_repo[row["repository"]].append(row)
    repositories = sorted(by_repo, key=lambda repo: (-len(by_repo[repo]), repo))
    selected: list[dict[str, Any]] = []
    scope_counts: Counter[str] = Counter()
    while len(selected) < count:
        progress = False
        for repository in repositories:
            bucket = by_repo[repository]
            chosen_index = None
            for index, row in enumerate(bucket):
                if row["commit"] in globally_used or row["parent"] in globally_used:
                    continue
                scope = subject_scope(row["subject"])
                if scope_counts[scope] < 5:
                    chosen_index = index
                    break
            if chosen_index is None:
                continue
            row = bucket.pop(chosen_index)
            scope_counts[subject_scope(row["subject"])] += 1
            selected.append(row)
            globally_used.add(row["commit"])
            globally_used.add(row["parent"])
            progress = True
            if len(selected) == count:
                break
        if not progress:
            break
    return selected


def eval_queue_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "candidate",
        "specialist": row["specialist"],
        "repository": row["repository"],
        "reference_commit": row["commit"],
        "start_commit": row["parent"],
        "subject": row["subject"],
        "changed_files": row["changed_files"],
        "inventory_score": row["score"],
        "review": {
            "reproducible": None,
            "focused": None,
            "objective_checks": None,
            "difficulty": None,
            "decision": None
        }
    }


def frontend_reaudit_rows() -> list[dict[str, Any]]:
    index = load_json(FRONTEND_INDEX)
    trajectories = load_jsonl(FRONTEND_KEEP)
    if len(index) != len(trajectories):
        raise SystemExit("frontend keep index and trajectory count differ")
    rows = []
    for keep_line, item in enumerate(index, 1):
        if item["score"] != 7:
            continue
        trajectory = trajectories[keep_line - 1]
        messages = trajectory.get("messages", [])
        prompt = next(
            (message.get("content", "") for message in messages if message.get("role") == "user"),
            "",
        )
        final = messages[-1].get("content", "") if messages else ""
        tool_calls = [
            call
            for message in messages
            if message.get("role") == "assistant"
            for call in message.get("tool_calls", [])
        ]
        bash_calls = [
            call for call in tool_calls if call.get("name") in {"bash", "shell", "run_command"}
        ]
        claim_text = final.lower()
        claims_verification = any(
            token in claim_text
            for token in ("test passes", "tests pass", "typecheck", "type check", "verified", "build passes", "clean")
        )
        claims_visual_observation = any(
            token in claim_text
            for token in ("screenshot", "visually confirmed", "observed in the browser", "dragged")
        )
        rows.append(
            {
                "schema_version": 1,
                "specialist": "frontend-stack",
                "v1_keep_line": keep_line,
                "v1_source": {
                    "batch": item["batch"],
                    "line": item["line"],
                    "score": item["score"]
                },
                "status": "pending",
                "evidence": {
                    "prompt_excerpt": prompt[:500],
                    "final_summary": final,
                    "tool_call_count": len(tool_calls),
                    "bash_call_count": len(bash_calls),
                    "claims_verification": claims_verification,
                    "unsupported_verification_risk": claims_verification and not bash_calls,
                    "fabricated_observation_risk": claims_visual_observation
                },
                "checks": {
                    "tool_trace_consistent": None,
                    "edit_matches_read_context": None,
                    "verification_supported": None,
                    "summary_truthful": None,
                    "decision": None
                }
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-candidates", type=int, default=40)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.eval_candidates < 20:
        parser.error("--eval-candidates must be at least 20")

    registry = load_json(REGISTRY)
    by_id = {item["id"]: item for item in registry["specialists"]}
    globally_used: set[str] = set()
    for specialist in QUEUE_ORDER:
        if by_id[specialist]["eval_state"] == "frozen":
            continue
        source_path = ROOT / "datasets" / specialist / "v2/sources/candidates.jsonl"
        if not source_path.is_file():
            raise SystemExit(f"missing inventory: {source_path.relative_to(ROOT)}")
        chosen = choose_eval_candidates(
            load_jsonl(source_path), args.eval_candidates, globally_used
        )
        if len(chosen) < 20:
            raise SystemExit(f"{specialist}: only {len(chosen)} usable eval candidates")
        output = ROOT / "evals/candidates" / f"{specialist}.jsonl"
        text = jsonl([eval_queue_row(row) for row in chosen])
        update_or_check(output, text, args.check)
        verb = "checked" if args.check else "wrote"
        print(f"{verb} {specialist}: {len(chosen)} eval candidates")

    reaudit = frontend_reaudit_rows()
    reaudit_path = ROOT / "datasets/frontend-stack/v2/review/score7-reaudit.jsonl"
    reaudit_text = jsonl(reaudit)
    update_or_check(reaudit_path, reaudit_text, args.check)
    manifest = {
        "schema_version": 1,
        "purpose": "semantic re-audit of every retained V1 score-7 frontend trajectory",
        "record_count": len(reaudit),
        "source": "datasets/frontend-stack/filtered/keep_ge7.index.json",
        "queue_sha256": hashlib.sha256(reaudit_text.encode("utf-8")).hexdigest(),
        "accept_rule": "all five checks true and decision=keep or repair",
    }
    update_or_check(
        reaudit_path.with_name("manifest.json"),
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        args.check,
    )
    verb = "checked" if args.check else "wrote"
    print(f"{verb} frontend-stack: {len(reaudit)} score-7 re-audit records")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
