"""Build deterministic, eval-safe source inventories for every V2 specialist.

The output is candidate metadata, not training data. New-domain training generation
must remain closed until its eval set is frozen in datasets/v2-registry.json.

    python scripts/build_v2_source_inventory.py
    python scripts/build_v2_source_inventory.py --check
    python scripts/build_v2_source_inventory.py --specialist security-review
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "datasets/v2-registry.json"
EVAL_ROOT = ROOT / "evals/tasks"
COMMIT_REF = re.compile(r"\bcommit\s+`([0-9a-fA-F]{7,40})`")
DOC_SUFFIXES = {
    ".md", ".mdx", ".txt", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
}


def run_git(repo: Path, *args: str, allow_failure: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode and not allow_failure:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git failed in {repo}: {detail}")
    return result.stdout.strip()


def load_registry(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read registry {path}: {exc}") from exc
    if data.get("schema_version") != 2:
        raise SystemExit("registry schema_version must be 2")
    return data


def eval_short_hashes() -> set[str]:
    hashes: set[str] = set()
    if not EVAL_ROOT.is_dir():
        return hashes
    for path in EVAL_ROOT.rglob("*.md"):
        hashes.update(match.lower() for match in COMMIT_REF.findall(path.read_text(encoding="utf-8")))
    return hashes


def reserved_hashes(repositories: dict[str, Any]) -> set[str]:
    """Expand committed eval refs to full reference commits and their parents."""
    reserved: set[str] = set()
    for short_hash in eval_short_hashes():
        for details in repositories.values():
            repo = Path(details["path"])
            if not (repo / ".git").exists():
                continue
            full = run_git(repo, "rev-parse", "--verify", f"{short_hash}^{{commit}}", allow_failure=True)
            if not re.fullmatch(r"[0-9a-f]{40}", full):
                continue
            reserved.add(full)
            parent = run_git(repo, "rev-parse", "--verify", f"{full}^", allow_failure=True)
            if re.fullmatch(r"[0-9a-f]{40}", parent):
                reserved.add(parent)
    return reserved


def log_records(repo: Path, max_commits: int) -> list[dict[str, Any]]:
    raw = run_git(
        repo,
        "log",
        "--all",
        "--no-merges",
        f"-n{max_commits}",
        "--format=%x1e%H%x1f%P%x1f%aI%x1f%s",
        "--name-only",
    )
    records: list[dict[str, Any]] = []
    for block in raw.split("\x1e"):
        lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
        if not lines:
            continue
        header = lines[0].split("\x1f", 3)
        if len(header) != 4:
            continue
        commit, parents, authored_at, subject = header
        parent_parts = parents.split()
        if not re.fullmatch(r"[0-9a-f]{40}", commit) or len(parent_parts) != 1:
            continue
        files = sorted(dict.fromkeys(line.replace("\\", "/") for line in lines[1:]))
        if files:
            records.append(
                {
                    "commit": commit,
                    "parent": parent_parts[0],
                    "authored_at": authored_at,
                    "subject": subject,
                    "changed_files": files,
                }
            )
    return records


def documentation_only(files: list[str]) -> bool:
    return all(
        Path(path).suffix.lower() in DOC_SUFFIXES
        or path.lower().startswith(("docs/", "plan/", "plans/"))
        for path in files
    )


def classify(record: dict[str, Any], specialist: dict[str, Any]) -> tuple[int, list[str]]:
    subject = record["subject"].lower()
    files = record["changed_files"]
    reasons: list[str] = []
    score = 0
    for keyword in specialist["subject_keywords"]:
        if keyword.lower() in subject:
            score += 3
            reasons.append(f"subject:{keyword}")
    for pattern in specialist["path_patterns"]:
        if any(re.search(pattern, path, flags=re.IGNORECASE) for path in files):
            score += 2
            reasons.append(f"path:{pattern}")
    if len(files) >= 2:
        score += 1
        reasons.append("multi-file")
    if len(files) > 20:
        score -= 2
        reasons.append("large-diff-penalty")
    return score, reasons


def render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )


def build_for_specialist(
    specialist: dict[str, Any],
    repositories: dict[str, Any],
    histories: dict[str, list[dict[str, Any]]],
    reserved: set[str],
) -> tuple[str, str]:
    rows: list[dict[str, Any]] = []
    for repository in specialist["sources"]:
        for record in histories[repository]:
            if record["commit"] in reserved or record["parent"] in reserved:
                continue
            if documentation_only(record["changed_files"]):
                continue
            score, reasons = classify(record, specialist)
            if score < 3:
                continue
            rows.append(
                {
                    "schema_version": 1,
                    "specialist": specialist["id"],
                    "repository": repository,
                    **record,
                    "score": score,
                    "reasons": reasons,
                }
            )
    rows.sort(key=lambda row: (-row["score"], row["repository"], row["commit"]))
    data_text = render_jsonl(rows)
    by_repo = Counter(row["repository"] for row in rows)
    manifest = {
        "schema_version": 1,
        "specialist": specialist["id"],
        "purpose": "source candidates only; not approved training data",
        "eval_state": specialist["eval_state"],
        "generation_gate": specialist["generation_gate"],
        "reserved_commit_count": len(reserved),
        "candidate_count": len(rows),
        "candidate_count_by_repository": dict(sorted(by_repo.items())),
        "source_heads": {
            repository: run_git(Path(repositories[repository]["path"]), "rev-parse", "HEAD")
            for repository in specialist["sources"]
        },
        "candidates_sha256": hashlib.sha256(data_text.encode("utf-8")).hexdigest(),
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return data_text, manifest_text


def update_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.is_file():
            raise SystemExit(f"missing generated file: {path.relative_to(ROOT)}")
        if path.read_text(encoding="utf-8") != content:
            raise SystemExit(f"stale generated file: {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--specialist", action="append", help="limit to one or more IDs")
    parser.add_argument("--max-commits", type=int, default=1000)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.max_commits <= 0:
        parser.error("--max-commits must be positive")

    registry = load_registry(args.registry)
    repositories = registry["source_repositories"]
    specialists = registry["specialists"]
    known = {item["id"] for item in specialists}
    requested = set(args.specialist or known)
    unknown = requested - known
    if unknown:
        parser.error(f"unknown specialist(s): {', '.join(sorted(unknown))}")
    specialists = [item for item in specialists if item["id"] in requested]

    needed_repositories = sorted({repo for item in specialists for repo in item["sources"]})
    histories: dict[str, list[dict[str, Any]]] = {}
    for name in needed_repositories:
        repo = Path(repositories[name]["path"])
        if not (repo / ".git").exists():
            raise SystemExit(f"missing Git repository {name}: {repo}")
        histories[name] = log_records(repo, args.max_commits)

    reserved = reserved_hashes(repositories)
    for specialist in specialists:
        data_text, manifest_text = build_for_specialist(
            specialist, repositories, histories, reserved
        )
        output = ROOT / "datasets" / specialist["id"] / "v2" / "sources"
        update_or_check(output / "candidates.jsonl", data_text, args.check)
        update_or_check(output / "manifest.json", manifest_text, args.check)
        count = data_text.count("\n")
        verb = "checked" if args.check else "wrote"
        print(f"{verb} {specialist['id']}: {count} candidates")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
