"""Validate V2 registry, source inventories, and any generated trajectories.

Missing not-yet-built trajectory files are reported as pending. Existing files are
strictly checked for structure, tool contracts, verification evidence, duplicates,
and overlap with frozen eval commits.

    python scripts/validate_v2_dataset.py --registry datasets/v2-registry.json
    python scripts/validate_v2_dataset.py --strict
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "datasets/v2-registry.json"
PI_TOOLS = ROOT / "training/pi_tools.json"
EVAL_ROOT = ROOT / "evals/tasks"
COMMIT_REF = re.compile(r"\bcommit\s+`([0-9a-fA-F]{7,40})`")
ID_PATTERN = re.compile(r"^[a-z0-9-]+:[a-z0-9._-]+$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{40}$")
TRAJECTORY_DIRS = ("generated", "filtered", "final")


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path}: invalid JSON: {exc}")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"{path}:{line_number}: invalid JSON: {exc}")
        if not isinstance(row, dict):
            fail(f"{path}:{line_number}: record must be an object")
        rows.append(row)
    return rows


def eval_refs() -> set[str]:
    refs: set[str] = set()
    if EVAL_ROOT.is_dir():
        for path in EVAL_ROOT.rglob("*.md"):
            refs.update(value.lower() for value in COMMIT_REF.findall(path.read_text(encoding="utf-8")))
    return refs


def overlaps_eval(full_hash: str, refs: set[str]) -> bool:
    return any(full_hash.startswith(ref) for ref in refs)


def validate_registry(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if registry.get("schema_version") != 2:
        fail("registry schema_version must be 2")
    if not isinstance(registry.get("source_repositories"), dict):
        fail("registry source_repositories must be an object")
    specialists = registry.get("specialists")
    if not isinstance(specialists, list) or not specialists:
        fail("registry specialists must be a non-empty list")
    indexed: dict[str, dict[str, Any]] = {}
    for item in specialists:
        specialist_id = item.get("id")
        if not isinstance(specialist_id, str) or specialist_id in indexed:
            fail(f"invalid or duplicate specialist id: {specialist_id!r}")
        if item.get("eval_state") not in {"frozen", "not_frozen"}:
            fail(f"{specialist_id}: invalid eval_state")
        expected = item.get("eval_task_count")
        task_dir = EVAL_ROOT / specialist_id
        actual = len(list(task_dir.glob("*.md"))) if task_dir.is_dir() else 0
        if expected != actual:
            fail(f"{specialist_id}: registry says {expected} eval tasks, found {actual}")
        if item["eval_state"] != "frozen" and item.get("generation_gate") == "open":
            fail(f"{specialist_id}: generation cannot open before eval freeze")
        unknown_sources = set(item.get("sources", [])) - set(registry["source_repositories"])
        if unknown_sources:
            fail(f"{specialist_id}: unknown sources {sorted(unknown_sources)}")
        indexed[specialist_id] = item
    return indexed


def validate_candidate(row: dict[str, Any], specialist: str, where: str, refs: set[str]) -> None:
    required = {
        "schema_version", "specialist", "repository", "commit", "parent", "subject",
        "authored_at", "changed_files", "score", "reasons",
    }
    if set(row) != required:
        fail(f"{where}: candidate fields differ: {sorted(set(row) ^ required)}")
    if row["schema_version"] != 1 or row["specialist"] != specialist:
        fail(f"{where}: wrong schema_version or specialist")
    if not HASH_PATTERN.fullmatch(row["commit"]) or not HASH_PATTERN.fullmatch(row["parent"]):
        fail(f"{where}: commit and parent must be full hashes")
    if overlaps_eval(row["commit"], refs) or overlaps_eval(row["parent"], refs):
        fail(f"{where}: overlaps a frozen eval commit")
    if not isinstance(row["changed_files"], list) or not row["changed_files"]:
        fail(f"{where}: changed_files must be non-empty")
    if not isinstance(row["score"], int) or row["score"] < 1:
        fail(f"{where}: invalid score")
    if not isinstance(row["reasons"], list) or not row["reasons"]:
        fail(f"{where}: reasons must be non-empty")


def validate_inventory(specialist: str, refs: set[str]) -> int:
    base = ROOT / "datasets" / specialist / "v2" / "sources"
    candidates_path = base / "candidates.jsonl"
    manifest_path = base / "manifest.json"
    if not candidates_path.is_file() or not manifest_path.is_file():
        print(f"pending {specialist}: source inventory")
        return 0
    rows = load_jsonl(candidates_path)
    seen: set[tuple[str, str]] = set()
    for number, row in enumerate(rows, 1):
        where = f"{candidates_path.relative_to(ROOT)}:{number}"
        validate_candidate(row, specialist, where, refs)
        identity = (row["repository"], row["commit"])
        if identity in seen:
            fail(f"{where}: duplicate repository commit")
        seen.add(identity)
    manifest = load_json(manifest_path)
    digest = hashlib.sha256(candidates_path.read_bytes()).hexdigest()
    if manifest.get("candidates_sha256") != digest:
        fail(f"{manifest_path}: candidates_sha256 mismatch")
    if manifest.get("candidate_count") != len(rows):
        fail(f"{manifest_path}: candidate_count mismatch")
    print(f"ok {specialist}: {len(rows)} source candidates")
    return len(rows)


def validate_eval_queues(
    indexed: dict[str, dict[str, Any]], selected: set[str], refs: set[str]
) -> None:
    used_hashes: set[str] = set()
    required = {
        "schema_version", "status", "specialist", "repository", "reference_commit",
        "start_commit", "subject", "changed_files", "inventory_score", "review",
    }
    for specialist in sorted(selected):
        if indexed[specialist]["eval_state"] == "frozen":
            continue
        path = ROOT / "evals/candidates" / f"{specialist}.jsonl"
        if not path.is_file():
            fail(f"{specialist}: missing eval candidate queue")
        rows = load_jsonl(path)
        if len(rows) < 20:
            fail(f"{path}: fewer than 20 eval candidates")
        for number, row in enumerate(rows, 1):
            where = f"{path.relative_to(ROOT)}:{number}"
            if set(row) != required:
                fail(f"{where}: invalid eval candidate fields")
            if (
                row["schema_version"] != 1
                or row["status"] != "candidate"
                or row["specialist"] != specialist
            ):
                fail(f"{where}: invalid queue identity")
            reference = row["reference_commit"]
            start = row["start_commit"]
            if (
                not isinstance(reference, str)
                or not isinstance(start, str)
                or not HASH_PATTERN.fullmatch(reference)
                or not HASH_PATTERN.fullmatch(start)
                or reference == start
            ):
                fail(f"{where}: invalid reference/start commit")
            if overlaps_eval(reference, refs) or overlaps_eval(start, refs):
                fail(f"{where}: overlaps an already frozen eval")
            if reference in used_hashes or start in used_hashes:
                fail(f"{where}: commit reused across eval queues")
            used_hashes.update((reference, start))
            review = row["review"]
            if not isinstance(review, dict) or set(review) != {
                "reproducible", "focused", "objective_checks", "difficulty", "decision"
            }:
                fail(f"{where}: invalid review fields")
        print(f"ok {specialist}: {len(rows)} eval candidates")


def canonical_messages(row: dict[str, Any]) -> str:
    return json.dumps(row["messages"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_tools(messages: list[Any], declared: set[str], where: str) -> dict[str, int]:
    successful_bash: dict[str, int] = {}
    index = 0
    while index < len(messages):
        message = messages[index]
        if not isinstance(message, dict) or message.get("role") not in {"system", "user", "assistant", "tool"}:
            fail(f"{where}: invalid message {index}")
        if message["role"] == "tool":
            fail(f"{where}: orphan tool result at message {index}")
        calls = message.get("tool_calls") if message["role"] == "assistant" else None
        if calls is None:
            index += 1
            continue
        if not isinstance(calls, list) or not calls:
            fail(f"{where}: invalid tool_calls at message {index}")
        results = messages[index + 1:index + 1 + len(calls)]
        if len(results) != len(calls):
            fail(f"{where}: incomplete tool results at message {index}")
        for call, result in zip(calls, results):
            if (
                not isinstance(call, dict)
                or set(call) != {"name", "arguments"}
                or call["name"] not in declared
                or not isinstance(call["arguments"], dict)
            ):
                fail(f"{where}: invalid tool call at message {index}")
            if (
                not isinstance(result, dict)
                or result.get("role") != "tool"
                or result.get("name") not in {None, "", call["name"]}
            ):
                fail(f"{where}: mismatched tool result at message {index}")
            if call["name"] == "bash":
                command = call["arguments"].get("command")
                metadata = result.get("metadata", {})
                if isinstance(command, str) and metadata.get("exit_code") == 0:
                    successful_bash[command] = successful_bash.get(command, 0) + 1
        index += 1 + len(calls)
    return successful_bash


def validate_trajectory(
    row: dict[str, Any],
    specialist: str,
    where: str,
    refs: set[str],
    pi_tools: list[dict[str, Any]],
) -> tuple[str, str]:
    required = {"id", "schema_version", "specialist", "source", "messages", "tools", "quality"}
    if set(row) != required:
        fail(f"{where}: trajectory fields differ: {sorted(set(row) ^ required)}")
    if row["schema_version"] != 2 or row["specialist"] != specialist:
        fail(f"{where}: wrong schema_version or specialist")
    if not isinstance(row["id"], str) or not ID_PATTERN.fullmatch(row["id"]):
        fail(f"{where}: invalid id")
    source = row["source"]
    if not isinstance(source, dict) or set(source) != {"repository", "commit", "parent", "files", "license"}:
        fail(f"{where}: invalid source object")
    for field in ("commit", "parent"):
        value = source.get(field)
        if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
            fail(f"{where}: source {field} must be a full hash")
        if overlaps_eval(value, refs):
            fail(f"{where}: source {field} overlaps frozen eval")
    if not isinstance(source.get("files"), list) or not source["files"]:
        fail(f"{where}: source files must be non-empty")
    messages = row["messages"]
    if not isinstance(messages, list) or len(messages) < 3:
        fail(f"{where}: messages must contain a complete trajectory")
    if messages[0].get("role") not in {"system", "user"} or messages[-1].get("role") != "assistant":
        fail(f"{where}: trajectory boundaries are invalid")
    if row["tools"] != pi_tools:
        fail(f"{where}: tools differ from training/pi_tools.json")
    declared = {tool["function"]["name"] for tool in row["tools"]}
    successful_bash = validate_tools(messages, declared, where)
    quality = row["quality"]
    required_quality = {"difficulty", "skills", "verification_commands", "review_state"}
    allowed_quality = required_quality | {"judge_score"}
    if not isinstance(quality, dict) or not required_quality <= set(quality) <= allowed_quality:
        fail(f"{where}: invalid quality fields")
    if quality["difficulty"] not in {"easy", "medium", "hard"}:
        fail(f"{where}: invalid difficulty")
    if quality["review_state"] not in {"generated", "judge_passed", "human_approved", "rejected"}:
        fail(f"{where}: invalid review_state")
    commands = quality["verification_commands"]
    if not isinstance(commands, list) or not commands or not all(isinstance(item, str) and item for item in commands):
        fail(f"{where}: verification_commands must be non-empty strings")
    missing = [command for command in commands if not successful_bash.get(command)]
    if missing:
        fail(f"{where}: verification lacks exit_code=0 evidence: {missing}")
    return row["id"], hashlib.sha256(canonical_messages(row).encode("utf-8")).hexdigest()


def trajectory_files(specialist: str) -> list[Path]:
    base = ROOT / "datasets" / specialist / "v2"
    files: list[Path] = []
    for directory in TRAJECTORY_DIRS:
        candidate = base / directory
        if candidate.is_dir():
            files.extend(sorted(candidate.glob("*.jsonl")))
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--specialist", action="append")
    parser.add_argument("--strict", action="store_true", help="require final train and holdout for selected domains")
    args = parser.parse_args()

    registry = load_json(args.registry)
    indexed = validate_registry(registry)
    selected = set(args.specialist or indexed)
    unknown = selected - set(indexed)
    if unknown:
        parser.error(f"unknown specialist(s): {', '.join(sorted(unknown))}")
    refs = eval_refs()
    pi_tools = load_json(PI_TOOLS)
    validate_eval_queues(indexed, selected, refs)
    total_trajectories = 0
    for specialist in sorted(selected):
        validate_inventory(specialist, refs)
        files = trajectory_files(specialist)
        if not files:
            if args.strict:
                fail(f"{specialist}: no V2 trajectory files")
            print(f"pending {specialist}: V2 trajectories")
            continue
        for path in files:
            rows = load_jsonl(path)
            file_ids: set[str] = set()
            file_content: set[str] = set()
            for number, row in enumerate(rows, 1):
                record_id, content_hash = validate_trajectory(
                    row, specialist, f"{path.relative_to(ROOT)}:{number}", refs, pi_tools
                )
                if record_id in file_ids:
                    fail(f"{path}:{number}: duplicate trajectory id {record_id}")
                if content_hash in file_content:
                    fail(f"{path}:{number}: duplicate normalized messages")
                file_ids.add(record_id)
                file_content.add(content_hash)
                total_trajectories += 1
        if args.strict:
            final = ROOT / "datasets" / specialist / "v2" / "final"
            for name in ("train.jsonl", "holdout.jsonl"):
                if not (final / name).is_file():
                    fail(f"{specialist}: missing final/{name}")
    print(f"validation ok: {len(selected)} specialists, {total_trajectories} V2 trajectories")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
