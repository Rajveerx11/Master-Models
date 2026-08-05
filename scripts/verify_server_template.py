"""Compare training-side Jinja rendering with llama-server `/apply-template`."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_train_mix import render

TRAIN = ROOT / "datasets/frontend-stack/final/train.jsonl"
JSON_BLOCK_RE = re.compile(r"(?P<open><tools>\n|<tool_call>\n)(?P<body>.*?)(?P<close>\n</tools>|\n</tool_call>)", re.S)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_json_blocks(prompt: str) -> str:
    """Canonicalize JSON-only lines while preserving all non-JSON prompt bytes."""

    def replace(match: re.Match) -> str:
        lines = match.group("body").splitlines()
        normalized = []
        for line in lines:
            try:
                normalized.append(json.dumps(json.loads(line), ensure_ascii=False, separators=(",", ":")))
            except json.JSONDecodeError:
                normalized.append(line)
        return match.group("open") + "\n".join(normalized) + match.group("close")

    return JSON_BLOCK_RE.sub(replace, prompt.replace("\r\n", "\n"))


def first_tool_record() -> dict:
    for raw in TRAIN.read_text(encoding="utf-8").splitlines():
        record = json.loads(raw)
        if record.get("tools") and any(message.get("tool_calls") for message in record["messages"]):
            return record
    raise SystemExit("training file has no structured tool-call record")


def apply_server(server: str, record: dict) -> str:
    body = {
        "messages": record["messages"],
        "tools": record["tools"],
        "add_generation_prompt": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = urllib.request.Request(
        server.rstrip("/") + "/apply-template",
        json.dumps(body).encode("utf-8"),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.load(response)
    return payload["prompt"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8081")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    record = first_tool_record()
    training_prompt = render(record["messages"], record["tools"])
    server_prompt = apply_server(args.server, record)
    exact = training_prompt == server_prompt
    normalized = normalize_json_blocks(training_prompt) == normalize_json_blocks(server_prompt)
    report = {
        "exact_match": exact,
        "json_whitespace_normalized_match": normalized,
        "training_sha256": sha256_text(training_prompt),
        "server_sha256": sha256_text(server_prompt),
        "training_chars": len(training_prompt),
        "server_chars": len(server_prompt),
    }
    print(json.dumps(report, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not normalized:
        diff = difflib.unified_diff(
            training_prompt.splitlines(), server_prompt.splitlines(),
            fromfile="training-jinja", tofile="llama-minja", n=2,
        )
        print("\n".join(list(diff)[:120]))
        raise SystemExit(1)
    if not exact:
        print("known engine-only JSON whitespace drift; normalized prompt is identical")


if __name__ == "__main__":
    main()
