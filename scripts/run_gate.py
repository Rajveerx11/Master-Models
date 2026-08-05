"""Run frozen frontend tasks through one live Neura/model arm.

Recommended setup:
  - llama-server for the selected model on 127.0.0.1:18081
  - scripts/gate_proxy.py on 127.0.0.1:18080
  - --server-url http://127.0.0.1:18080

The CLI default remains 8080 for backward compatibility. The dedicated provider used
by this gate defaults to 18080, so pass --server-url explicitly.

The runner never checks out or edits the source repositories. Each task gets a
depth-1 isolated repository containing only its recorded start commit, preventing
future/reference commits from leaking to the model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "evals/tasks/frontend-stack"
DEFAULT_PI = Path(os.environ.get("APPDATA", "")) / "npm/pi.cmd"
GATE_PROVIDER = ROOT / "scripts/gate_provider.ts"
SOURCE_RE = re.compile(r"^Source: `(?P<repo>[^`]+)` commit `(?P<commit>[0-9a-f]+)`", re.M)
START_RE = re.compile(r"^Start state: `git -C \"[^\"]+\" checkout (?P<revision>[^`]+)`", re.M)
PROMPT_RE = re.compile(r"## Prompt \(given to the agent verbatim\)\s*(.*?)\s*## Success criteria", re.S)


def run(command: list[str], cwd: Path | None = None, timeout: int = 300, check: bool = True):
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=check,
    )


def git(repo: Path, *args: str, timeout: int = 300, check: bool = True):
    return run(["git", "-C", str(repo), *args], timeout=timeout, check=check)


def parse_task(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    source = SOURCE_RE.search(text)
    start = START_RE.search(text)
    prompt = PROMPT_RE.search(text)
    if not (source and start and prompt):
        raise ValueError(f"cannot parse frozen task: {path}")
    return {
        "number": int(path.name[:2]),
        "file": path,
        "repo": Path(source.group("repo")),
        "reference_commit": source.group("commit"),
        "start_revision": start.group("revision"),
        "prompt": prompt.group(1).strip(),
    }


def select_tasks(spec: str) -> list[dict]:
    tasks = {int(path.name[:2]): parse_task(path) for path in TASKS_DIR.glob("[0-9][0-9]-*.md")}
    if spec == "all":
        wanted = sorted(tasks)
    else:
        wanted: list[int] = []
        for part in spec.split(","):
            if "-" in part:
                first, last = map(int, part.split("-", 1))
                wanted.extend(range(first, last + 1))
            else:
                wanted.append(int(part))
    missing = [number for number in wanted if number not in tasks]
    if missing:
        raise SystemExit(f"unknown task numbers: {missing}")
    return [tasks[number] for number in dict.fromkeys(wanted)]


def resolve_start(task: dict) -> str:
    result = run(
        ["git", "-C", str(task["repo"]), "rev-parse", "--verify", f"{task['start_revision']}^{{commit}}"],
    )
    return result.stdout.strip()


def isolated_checkout(task: dict, target: Path) -> str:
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing run directory: {target}")
    target.mkdir(parents=True)
    run(["git", "init", "--quiet", str(target)])
    start_hash = resolve_start(task)
    # Fetch exactly the start commit. No branches, tags, remotes, or future commits
    # enter the clone, so `git log --all` cannot reveal the graders-only solution.
    git(target, "fetch", "--quiet", "--depth=1", "--no-tags", str(task["repo"]), start_hash, timeout=600)
    git(target, "checkout", "--quiet", "--detach", "FETCH_HEAD")
    return start_hash


def server_ready(url: str) -> dict:
    with urllib.request.urlopen(url.rstrip("/") + "/v1/models", timeout=10) as response:
        return json.load(response)


def invoke_pi(pi_cmd: Path, cwd: Path, prompt_file: Path, stdout_path: Path, stderr_path: Path, timeout: int) -> int:
    if not pi_cmd.is_file():
        raise FileNotFoundError(f"pi launcher missing: {pi_cmd}")
    args = [
        str(pi_cmd),
        "--extension", str(GATE_PROVIDER),
        "--mode", "json",
        "--print",
        "--no-session",
        "--provider", "master-models-gate",
        "--model", "frontend-stack-gate",
        "--thinking", "off",
        "--approve",
        f"@{prompt_file}",
        "Complete the attached task. Inspect the repository, make the change, and verify it.",
    ]
    env = os.environ.copy()
    env["NEURA"] = "1"
    env["PYTHONUTF8"] = "1"
    # Batch launchers require cmd.exe on Windows. list2cmdline preserves the
    # absolute @prompt path and avoids putting task prose into shell syntax.
    command = ["cmd.exe", "/d", "/s", "/c", subprocess.list2cmdline(args)]
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout, stderr_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as stderr:
        completed = subprocess.run(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
    return completed.returncode


def install_dependencies(cwd: Path, log_path: Path, timeout: int = 900) -> tuple[int, float]:
    """Prepare an isolated checkout before the model sees it.

    The frozen source repositories intentionally do not contain node_modules. Every
    arm gets the same lockfile-frozen install, and pnpm's shared store makes later
    arms cheap while keeping source repositories untouched.
    """
    started = time.time()
    completed = run(
        [
            "cmd.exe", "/d", "/c", "pnpm", "install",
            "--frozen-lockfile", "--prefer-offline",
        ],
        cwd=cwd,
        timeout=timeout,
        check=False,
    )
    log_path.write_text(
        completed.stdout + completed.stderr, encoding="utf-8", newline="\n"
    )
    return completed.returncode, round(time.time() - started, 1)


def parse_tool_metrics(path: Path) -> dict:
    starts: Counter[str] = Counter()
    ends = errors = malformed_lines = 0
    stop_reasons: Counter[str] = Counter()
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            malformed_lines += 1
            continue
        kind = event.get("type")
        if kind == "tool_execution_start":
            starts[event.get("toolName") or "unknown"] += 1
        elif kind == "tool_execution_end":
            ends += 1
            errors += int(bool(event.get("isError")))
        elif kind == "message_end":
            message = event.get("message") or {}
            if message.get("role") == "assistant" and message.get("stopReason"):
                stop_reasons[message["stopReason"]] += 1
    return {
        "tool_calls": sum(starts.values()),
        "tool_names": dict(starts),
        "tool_results": ends,
        "tool_errors": errors,
        "json_stream_malformed_lines": malformed_lines,
        "assistant_stop_reasons": dict(stop_reasons),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["A", "B", "C"], required=True)
    ap.add_argument("--tasks", default="all", help="all, 1,3,5, or ranges such as 1-5")
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--server-url", default="http://127.0.0.1:8080")
    ap.add_argument("--pi", type=Path, default=DEFAULT_PI)
    ap.add_argument("--timeout", type=int, default=3600, help="seconds per agent task")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--resume", action="store_true", help="continue a matching existing run")
    args = ap.parse_args()

    if not args.model_path.is_file():
        raise SystemExit(f"model does not exist: {args.model_path}")
    models = server_ready(args.server_url)
    run_id = args.run_id or f"{date.today().isoformat()}-frontend-stack-arm-{args.arm.lower()}"
    root = ROOT / "outputs/gate" / run_id
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    resolved_model = str(args.model_path.resolve())
    if manifest_path.exists():
        if not args.resume:
            raise SystemExit(f"run already exists: {root} (pass --resume to continue it)")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = {
            "arm": args.arm,
            "model_path": resolved_model,
            "model_sha256": sha256(args.model_path),
            "tasks": args.tasks,
        }
        mismatches = {
            key: (manifest.get(key), value)
            for key, value in expected.items()
            if manifest.get(key) != value
        }
        if mismatches:
            raise SystemExit(f"refusing to resume mismatched run: {mismatches}")
    else:
        if args.resume:
            raise SystemExit(f"cannot resume; manifest does not exist: {manifest_path}")
        manifest = {
            "run_id": run_id,
            "arm": args.arm,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "model_path": resolved_model,
            "model_sha256": sha256(args.model_path),
            "server_url": args.server_url,
            "server_models": models,
            "pi": str(args.pi),
            "neura_source_commit": run(["git", "-C", "C:/Neura", "rev-parse", "HEAD"]).stdout.strip(),
            "tasks": args.tasks,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for task in select_tasks(args.tasks):
        label = task["file"].stem
        result_dir = root / label
        if result_dir.exists():
            result_path = result_dir / "result.json"
            if args.resume and result_path.is_file():
                print(f"arm {args.arm} task {task['number']:02}: already complete; skipped")
                continue
            raise SystemExit(f"incomplete task directory needs inspection: {result_dir}")
        checkout = result_dir / "repo"
        result_dir.mkdir(parents=True)
        prompt_path = result_dir / "prompt.md"
        prompt_path.write_text(task["prompt"] + "\n", encoding="utf-8")
        started = time.time()
        result = {
            "task": task["number"],
            "task_file": str(task["file"].relative_to(ROOT)),
            "source_repo": str(task["repo"]),
            "reference_commit": task["reference_commit"],
            "arm": args.arm,
            "grade": "ungraded",
        }
        try:
            start_hash = isolated_checkout(task, checkout)
            result["start_commit"] = start_hash
            install_code, install_s = install_dependencies(
                checkout, result_dir / "dependency-install.log"
            )
            result["dependency_install_exit_code"] = install_code
            result["dependency_install_s"] = install_s
            if install_code != 0:
                raise RuntimeError(
                    "lockfile-frozen dependency install failed; see dependency-install.log"
                )
            stdout_path = result_dir / "agent.jsonl"
            stderr_path = result_dir / "agent.stderr.log"
            result["agent_exit_code"] = invoke_pi(
                args.pi, checkout, prompt_path.resolve(), stdout_path, stderr_path, args.timeout
            )
            result["tool_metrics"] = parse_tool_metrics(stdout_path)
            result["status"] = git(checkout, "status", "--short").stdout.splitlines()
            untracked = git(
                checkout, "ls-files", "--others", "--exclude-standard"
            ).stdout.splitlines()
            result["untracked_files"] = untracked
            if untracked:
                # Intent-to-add makes new files appear in the archival patch without
                # staging their content or changing the source repository.
                git(checkout, "add", "--intent-to-add", "--", *untracked)
            diff = git(checkout, "diff", "--binary", start_hash, "--", timeout=300).stdout
            (result_dir / "changes.patch").write_text(diff, encoding="utf-8", newline="\n")
            result["changed"] = bool(diff.strip())

            typecheck = run(
                ["cmd.exe", "/d", "/c", "pnpm", "exec", "tsc", "--noEmit"],
                cwd=checkout,
                timeout=900,
                check=False,
            )
            (result_dir / "typecheck.log").write_text(
                typecheck.stdout + typecheck.stderr, encoding="utf-8", newline="\n"
            )
            result["typecheck_exit_code"] = typecheck.returncode
        except subprocess.TimeoutExpired as error:
            result["error"] = f"timeout after {error.timeout}s"
        except Exception as error:
            result["error"] = f"{type(error).__name__}: {error}"
        dependency_dir = checkout / "node_modules"
        result["dependency_tree_removed"] = False
        if dependency_dir.is_dir():
            cleanup_started = time.time()
            try:
                shutil.rmtree(dependency_dir)
                result["dependency_tree_removed"] = True
                result["dependency_cleanup_s"] = round(time.time() - cleanup_started, 1)
            except Exception as error:
                result["dependency_cleanup_error"] = f"{type(error).__name__}: {error}"
        result["elapsed_s"] = round(time.time() - started, 1)
        (result_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"arm {args.arm} task {task['number']:02}: {result.get('agent_exit_code', 'ERR')} ({result['elapsed_s']}s)")


if __name__ == "__main__":
    sys.exit(main())
