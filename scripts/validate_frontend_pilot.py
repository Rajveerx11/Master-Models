"""Check the curated frontend pilot's source identity and pending-only status.

Read-only metadata validation; this never executes a task or approves training.
    py -3 scripts/validate_frontend_pilot.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

try:
    from .build_v2_source_inventory import reserved_hashes
except ImportError:
    from build_v2_source_inventory import reserved_hashes

ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / "datasets/frontend-stack/v2/review/pilot"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    registry = json.loads((ROOT / "datasets/v2-registry.json").read_text(encoding="utf-8"))
    repositories = registry["source_repositories"]
    manifest = json.loads((PILOT / "manifest.json").read_text(encoding="utf-8"))
    tasks = read_jsonl(PILOT / "tasks.jsonl")
    inventory_path = ROOT / "datasets/frontend-stack/v2/sources/candidates.jsonl"
    inventory = {(row["repository"], row["commit"]): row for row in read_jsonl(inventory_path)}
    for key, path in [("tasks_sha256", PILOT / "tasks.jsonl"),
                      ("inventory_sha256", inventory_path),
                      ("exclusions_sha256", PILOT / "eval-exclusions.json")]:
        require(manifest[key] == sha(path.read_bytes()), f"stale pilot hash: {path}")
    frozen_paths = {p.relative_to(ROOT).as_posix() for p in (ROOT / "evals/tasks").rglob("*.md")}
    require(frozen_paths == set(manifest["frozen_eval_hashes"]), "frozen eval file set changed")
    for path, expected in manifest["frozen_eval_hashes"].items():
        require(sha((ROOT / path).read_bytes()) == expected, f"frozen eval changed: {path}")
    require(len(tasks) == manifest["selected_tasks"] == 30, "pilot must contain 30 tasks")
    require(len(inventory) == manifest["corrected_frontend_candidates"] == 143, "inventory count changed; re-review pilot")
    require(manifest["gold_approved"] == manifest["executed_tasks"] == 0 and manifest["training_eligible"] is False,
            "selection manifest must not assert execution or training approval")
    require(dict(Counter(t["repository"] for t in tasks)) == manifest["source_repositories"], "repository counts differ")
    require(dict(Counter(t["coverage"] for t in tasks)) == manifest["coverage"], "coverage counts differ")
    reserved = reserved_hashes(repositories)
    exclusions = json.loads((PILOT / "eval-exclusions.json").read_text(encoding="utf-8"))
    require(len(exclusions) == manifest["eval_excluded"] == 60, "exclusion count differs")
    require(len({(r['repository'], r['commit']) for r in exclusions}) == 60, "duplicate exclusion")
    for row in exclusions:
        require(set(row["reserved_matches"]) == ({row["commit"], row["parent"]} & reserved)
                and bool(row["reserved_matches"]), "exclusion no longer matches frozen eval")
        require((row["repository"], row["commit"]) not in inventory, "excluded commit returned to inventory")
    for row in inventory.values():
        require(not ({row["commit"], row["parent"]} & reserved), "inventory still overlaps eval")

    def git(repo: str, *args: str) -> bytes:
        return subprocess.check_output(["git", "-C", repositories[repo]["path"], *args])

    ids, refs, prompts = set(), set(), set()
    for task in tasks:
        label = task["id"]
        repo, parent, reference = task["repository"], task["parent"], task["reference_commit"]
        require(label not in ids and (repo, reference) not in refs and task["prompt"] not in prompts,
                f"duplicate pilot identity: {label}")
        ids.add(label)
        refs.add((repo, reference))
        prompts.add(task["prompt"])
        require((repo, reference) in inventory, f"{label}: absent from reviewed inventory")
        require(inventory[(repo, reference)]["parent"] == parent, f"{label}: wrong inventory parent")
        require(git(repo, "rev-parse", f"{reference}^{{commit}}").decode().strip() == reference,
                f"{label}: not full reference hash")
        parents = git(repo, "show", "-s", "--format=%P", reference).decode().split()
        require(parents == [parent], f"{label}: source must have exactly the recorded parent")
        require(not ({parent, reference} & reserved), f"{label}: overlaps frozen eval")
        require(task["training_eligible"] is False and task["execution_state"] == "not_started"
                and task["independent_semantic_review"] == "pending" and task["split"] == "unassigned"
                and task["selection_state"] == "selected_for_pilot", f"{label}: selection is not gold")
        require(len(task["acceptance_checks"]) >= 3 and task["expected_baseline"]
                and task["reviewer_notes"] and task["split_group"], f"{label}: missing review specification")
        require(task["verification_plan"]["state"] == "specified_not_executed", f"{label}: wrong verification state")
        full = git(repo, "diff", "--no-ext-diff", "--binary", parent, reference)
        scoped = git(repo, "diff", "--no-ext-diff", "--binary", parent, reference, "--", *task["scope_paths"])
        require(sha(full) == task["reference_diff_sha256"] and sha(scoped) == task["scoped_diff_sha256"],
                f"{label}: source patch hash changed")
        changed = set(git(repo, "diff", "--name-only", parent, reference).decode().splitlines())
        require(set(task["scope_paths"]) <= changed and len(task["scope_paths"]) == len(set(task["scope_paths"])),
                f"{label}: scope is not a unique subset of source changed paths")
        require(set(task["source_files"]) == set(task["scope_paths"]), f"{label}: blob evidence incomplete")
        for path, blobs in task["source_files"].items():
            for field, revision in [("parent_blob", parent), ("reference_blob", reference)]:
                result = git(repo, "ls-tree", revision, "--", path).decode().split()
                require(blobs[field] == (result[2] if result else None), f"{label}: wrong blob for {path}")
        require({"package.json", "pnpm-lock.yaml"} <= set(task["dependency_inputs"]),
                f"{label}: dependency provenance incomplete")
        for path, expected in task["dependency_inputs"].items():
            require(sha(git(repo, "show", f"{parent}:{path}")) == expected, f"{label}: dependency input changed: {path}")
    print(f"pilot selection valid: {len(tasks)} tasks, {len(reserved)} reserved eval hashes, 0 executed / 0 gold")


if __name__ == "__main__":
    main()
