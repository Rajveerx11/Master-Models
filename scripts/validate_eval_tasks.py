"""Validate frozen repository-task metadata and Git ancestry.

This validator never checks out or edits a source repository.

    py -3 scripts/validate_eval_tasks.py
    py -3 scripts/validate_eval_tasks.py --require-v2
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "datasets/v2-registry.json"
TASK_ROOT = ROOT / "evals/tasks"
V2_DOMAINS = ("backend-stack", "security-review", "code-review", "testing-qa")
SOURCE = re.compile(
    r"^Source:\s+`([^`]+)`\s+commit\s+`([0-9a-fA-F]{7,40})`",
    re.MULTILINE,
)
V2_REPOSITORY = re.compile(r"^Source repository:\s+`([a-z0-9-]+)`", re.MULTILINE)
V2_CHECKOUT = re.compile(r"^Source checkout:\s+`([^`]+)`", re.MULTILINE)
V2_REFERENCE = re.compile(r"^Reference commit:\s+`([0-9a-fA-F]{40})`", re.MULTILINE)
V2_START = re.compile(r"^Start commit:\s+`([0-9a-fA-F]{40})`", re.MULTILINE)
DIFFICULTY = re.compile(r"^Difficulty:\s+\*\*(easy|medium|hard)\*\*", re.MULTILINE)
START = re.compile(
    r"^Start state:\s+`git\s+-C\s+.+?\s+checkout\s+([0-9a-fA-F]{7,40}(?:~1|\^)?)`",
    re.MULTILINE,
)
TASK_MODE = re.compile(r"^Task mode:\s+\*\*(implementation|review)\*\*", re.MULTILINE)
PATCH_BASE = re.compile(r"^Patch base:\s+`([0-9a-fA-F]{7,40})`", re.MULTILINE)
PATCH_TARGET = re.compile(r"^Patch target:\s+`([0-9a-fA-F]{7,40})`", re.MULTILINE)
PATCH_DIRECTION = re.compile(
    r"^Patch direction:\s+\*\*(defective-reverse|clean-forward)\*\*",
    re.MULTILINE,
)
PROMPT = re.compile(
    r"## Prompt \(given to the agent verbatim\)\s+(.+?)\s+## Success criteria",
    re.DOTALL,
)


def fail(message: str) -> None:
    raise SystemExit(message)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        fail(f"git failed in {repo}: {result.stderr.strip()}")
    return result.stdout.strip()


def canonical_repo(path_text: str, repositories: dict[str, Any]) -> tuple[str, Path]:
    candidate = Path(path_text.strip())
    candidate_text = str(candidate.resolve()).lower()
    for name, details in repositories.items():
        path = Path(details["path"])
        if str(path.resolve()).lower() == candidate_text:
            return name, path
    fail(f"unregistered source repository: {path_text}")


def parse_task(path: Path, repositories: dict[str, Any]) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    for heading in (
        "## Prompt (given to the agent verbatim)",
        "## Success criteria (checkable)",
        "## Scoring: pass / partial / fail notes",
    ):
        if heading not in text:
            fail(f"{path}: missing heading {heading!r}")
    source = SOURCE.search(text)
    v2_repository = V2_REPOSITORY.search(text)
    v2_checkout = V2_CHECKOUT.search(text)
    v2_reference = V2_REFERENCE.search(text)
    difficulty = DIFFICULTY.search(text)
    prompt = PROMPT.search(text)
    if not difficulty or not prompt:
        fail(f"{path}: cannot parse source, difficulty, or prompt")
    if source:
        repository, repo_path = canonical_repo(source.group(1), repositories)
        reference_text = source.group(2)
    elif v2_repository and v2_checkout and v2_reference:
        repository = v2_repository.group(1)
        if repository not in repositories:
            fail(f"{path}: unregistered repository id {repository}")
        registered, repo_path = canonical_repo(v2_checkout.group(1), repositories)
        if registered != repository:
            fail(f"{path}: repository id and checkout disagree")
        reference_text = v2_reference.group(1)
        if "## Verification commands" not in text:
            fail(f"{path}: V2 task lacks verification commands")
    else:
        fail(f"{path}: cannot parse source metadata")
    reference = git(repo_path, "rev-parse", "--verify", f"{reference_text}^{{commit}}")
    parent = git(repo_path, "rev-parse", "--verify", f"{reference}^")
    mode_match = TASK_MODE.search(text)
    mode = mode_match.group(1) if mode_match else "implementation"
    if mode == "review":
        base_match = PATCH_BASE.search(text)
        target_match = PATCH_TARGET.search(text)
        direction_match = PATCH_DIRECTION.search(text)
        if not base_match or not target_match or not direction_match:
            fail(f"{path}: review task lacks patch base, target, or direction")
        base = git(repo_path, "rev-parse", "--verify", f"{base_match.group(1)}^{{commit}}")
        target = git(repo_path, "rev-parse", "--verify", f"{target_match.group(1)}^{{commit}}")
        if direction_match.group(1) == "clean-forward" and (base, target) != (parent, reference):
            fail(f"{path}: clean-forward patch must be parent -> reference")
        if direction_match.group(1) == "defective-reverse" and (base, target) != (reference, parent):
            fail(f"{path}: defective-reverse patch must be reference -> parent")
        start_hash = parent
    else:
        start = START.search(text)
        v2_start = V2_START.search(text)
        if start:
            start_text = start.group(1)
        elif v2_start:
            start_text = v2_start.group(1)
        else:
            fail(f"{path}: implementation task lacks start state")
        start_hash = git(repo_path, "rev-parse", "--verify", f"{start_text}^{{commit}}")
        if start_hash != parent:
            fail(f"{path}: start commit is not the reference commit's single parent")
    if len(prompt.group(1).strip()) < 30:
        fail(f"{path}: prompt is too short")
    if len(re.findall(r"^- \[ \]", text, flags=re.MULTILINE)) < 3:
        fail(f"{path}: fewer than three checkable success criteria")
    if "graders only" not in text.lower() and "graders-only" not in text.lower():
        fail(f"{path}: missing graders-only reference evidence")
    return {
        "repository": repository,
        "reference": reference,
        "start": start_hash,
        "difficulty": difficulty.group(1),
        "mode": mode,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-v2", action="store_true")
    parser.add_argument("--domain", action="append", help="validate only selected domain(s)")
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    repositories = registry["source_repositories"]
    configured = {item["id"]: item for item in registry["specialists"]}
    selected = set(args.domain or configured)
    unknown = selected - set(configured)
    if unknown:
        parser.error(f"unknown domain(s): {', '.join(sorted(unknown))}")
    used_references: dict[str, Path] = {}
    used_v2_hashes: dict[str, Path] = {}
    total_tasks = 0
    for domain in configured:
        if domain not in selected:
            continue
        directory = TASK_ROOT / domain
        files = sorted(directory.glob("*.md")) if directory.is_dir() else []
        if args.require_v2 and domain in V2_DOMAINS and len(files) != 20:
            fail(f"{domain}: require-v2 expected 20 tasks, found {len(files)}")
        expected = configured[domain]["eval_task_count"]
        if configured[domain]["eval_state"] == "frozen" and len(files) != expected:
            fail(f"{domain}: frozen registry count {expected}, found {len(files)}")
        if not files:
            print(f"pending {domain}: no frozen tasks")
            continue
        records = [parse_task(path, repositories) for path in files]
        if len(files) == 20:
            counts = Counter(record["difficulty"] for record in records)
            if counts != Counter({"easy": 5, "medium": 9, "hard": 6}):
                fail(f"{domain}: wrong difficulty balance {dict(counts)}")
        for path, record in zip(files, records):
            reference = record["reference"]
            if reference in used_references:
                fail(f"{path}: reference commit reused by {used_references[reference]}")
            used_references[reference] = path
            if domain in V2_DOMAINS:
                for field in ("reference", "start"):
                    value = record[field]
                    if value in used_v2_hashes:
                        fail(f"{path}: {field} commit reused by {used_v2_hashes[value]}")
                    used_v2_hashes[value] = path
            total_tasks += 1
        print(f"ok {domain}: {len(files)} tasks")
    print(f"eval validation ok: {total_tasks} tasks")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
