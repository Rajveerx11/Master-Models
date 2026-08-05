"""Build a whole-record, token-capped QLoRA training split.

No rendered text or message is sliced. Records pass only when their exact pinned-Qwen
render is within the cap, preserving every assistant tool-call/tool-result pair.
The frozen holdout is never a candidate; duplicate records fail the build.

    python scripts/build_short_train.py
    python scripts/build_short_train.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "datasets/frontend-stack/final/train.jsonl"
HOLDOUT = ROOT / "datasets/frontend-stack/final/holdout.jsonl"
OUT = ROOT / "datasets/frontend-stack/final/train-short4096.jsonl"
HOLDOUT_OUT = ROOT / "datasets/frontend-stack/final/holdout-short4096.jsonl"
MANIFEST = ROOT / "datasets/frontend-stack/final/train-short4096.manifest.json"
TEMPLATE = ROOT / "training/templates/qwen3-8b.jinja"
# Tokenizer files are already present with the Unsloth 4-bit training base.
TOKENIZER = "unsloth/Qwen3-8B-unsloth-bnb-4bit"
CAP = 4096
# TRL appends the terminal <|im_end|> token to a pre-rendered text field. Count its
# one-token overhead here, rather than trusting a shorter transformers-only length.
SFT_TERMINAL_OVERHEAD = 1


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fingerprint(row: dict[str, Any]) -> str:
    return sha256_text(canonical(row))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise SystemExit(f"missing JSONL: {path}")
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{line_no}: record must be an object")
        rows.append(row)
    if not rows:
        raise SystemExit(f"{path}: no records")
    return rows


def check_trajectory(row: dict[str, Any], where: str) -> None:
    """Every emitted tool call has its complete, matching contiguous result set."""
    tools = row.get("tools")
    declared_names = None
    if tools is not None:
        if not isinstance(tools, list) or not tools:
            raise SystemExit(f"{where}: tools must be a non-empty list when present")
        declared_names = set()
        for tool_no, tool in enumerate(tools, 1):
            function = tool.get("function") if isinstance(tool, dict) else None
            if (
                not isinstance(function, dict)
                or not isinstance(function.get("name"), str)
                or not function["name"]
                or not isinstance(function.get("parameters", {}), dict)
            ):
                raise SystemExit(f"{where}: invalid tool schema at tools[{tool_no}]")
            declared_names.add(function["name"])
    messages = row.get("messages")
    if not isinstance(messages, list) or not messages:
        raise SystemExit(f"{where}: messages must be a non-empty list")
    if messages[0].get("role") not in {"system", "user"}:
        raise SystemExit(f"{where}: first message must be system or user")
    if messages[-1].get("role") != "assistant":
        raise SystemExit(f"{where}: final message must be assistant")
    index = 0
    while index < len(messages):
        message = messages[index]
        if not isinstance(message, dict) or message.get("role") not in {"system", "user", "assistant", "tool"}:
            raise SystemExit(f"{where}: invalid role at message {index}")
        if message.get("role") == "tool":
            raise SystemExit(f"{where}: orphan tool result at message {index}")
        calls = message.get("tool_calls") if message.get("role") == "assistant" else None
        if calls is None:
            index += 1
            continue
        if not isinstance(calls, list) or not calls:
            raise SystemExit(f"{where}: invalid tool_calls at message {index}")
        results = messages[index + 1:index + 1 + len(calls)]
        if len(results) != len(calls):
            raise SystemExit(f"{where}: incomplete result set after message {index}")
        for offset, (call, result) in enumerate(zip(calls, results), 1):
            if not isinstance(call, dict) or not call.get("name") or not isinstance(call.get("arguments"), dict):
                raise SystemExit(f"{where}: invalid tool call {offset} at message {index}")
            if declared_names is not None and call["name"] not in declared_names:
                raise SystemExit(f"{where}: undeclared tool {call['name']!r} at message {index}")
            if not isinstance(result, dict) or result.get("role") != "tool":
                raise SystemExit(f"{where}: missing tool result {offset} at message {index}")
            if result.get("name") not in {None, "", call["name"]}:
                raise SystemExit(f"{where}: tool result {offset} mismatches message {index}")
        index += 1 + len(calls)


def load_tokenizer(model_id: str, template: str, allow_download: bool):
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise SystemExit("transformers unavailable; run inside Unsloth environment") from exc
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=not allow_download)
    except OSError as exc:
        raise SystemExit(f"cannot load tokenizer {model_id!r}: {exc}") from exc
    tokenizer.chat_template = template
    return tokenizer


def token_count(tokenizer, row: dict[str, Any]) -> int:
    rendered = tokenizer.apply_chat_template(
        row["messages"], tools=row.get("tools") or None, tokenize=False,
        add_generation_prompt=False, enable_thinking=False,
    )
    if not rendered.strip():
        raise SystemExit("empty rendered record")
    if row.get("tools") and "<tools>" not in rendered:
        raise SystemExit("tool-bearing record rendered without <tools>")
    return len(tokenizer(rendered).input_ids) + SFT_TERMINAL_OVERHEAD


def rows_text(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)


def split_report(rows: list[dict[str, Any]], total: int, lengths: list[int], output: str) -> dict[str, Any]:
    return {
        "input_records": total,
        "retained_records": len(rows),
        "dropped_over_cap": total - len(rows),
        "retained_by_source": dict(sorted(Counter(str(r.get("source", "unknown")) for r in rows).items())),
        "rendered_tokens": {"min": min(lengths), "max": max(lengths), "mean": round(sum(lengths) / len(lengths), 3)},
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }


def manifest(
    train: Path, holdout: Path, train_rows: list[dict[str, Any]], holdout_rows: list[dict[str, Any]],
    train_total: int, holdout_total: int, cap: int, tokenizer_id: str, template: str,
    train_lengths: list[int], holdout_lengths: list[int], train_output: str, holdout_output: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "selection": "whole-record filter; no message or text truncation",
        "token_cap": cap,
        "tokenizer": tokenizer_id,
        "token_counting": "pinned apply_chat_template(add_generation_prompt=False, enable_thinking=False), tokenizer(rendered), plus TRL terminal <|im_end|>",
        "template_sha256": hashlib.sha256(template.encode("utf-8")).hexdigest(),
        "source_train": str(train.relative_to(ROOT)),
        "source_train_sha256": hashlib.sha256(train.read_bytes()).hexdigest(),
        "frozen_holdout": str(holdout.relative_to(ROOT)),
        "frozen_holdout_sha256": hashlib.sha256(holdout.read_bytes()).hexdigest(),
        "training_split": split_report(train_rows, train_total, train_lengths, train_output),
        "holdout_split": split_report(holdout_rows, holdout_total, holdout_lengths, holdout_output),
    }


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=TRAIN)
    parser.add_argument("--holdout", type=Path, default=HOLDOUT)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--holdout-out", type=Path, default=HOLDOUT_OUT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--cap", type=int, default=CAP)
    parser.add_argument("--tokenizer", default=TOKENIZER)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.cap <= 0:
        parser.error("--cap must be positive")

    template = TEMPLATE.read_text(encoding="utf-8")
    tokenizer = load_tokenizer(args.tokenizer, template, args.allow_download)
    source, holdout = read_jsonl(args.train), read_jsonl(args.holdout)
    holdout_fingerprints = {fingerprint(row) for row in holdout}
    kept, lengths, kept_holdout, holdout_lengths = [], [], [], []
    for line_no, row in enumerate(source, 1):
        where = f"{args.train}:{line_no}"
        check_trajectory(row, where)
        if fingerprint(row) in holdout_fingerprints:
            raise SystemExit(f"{where}: duplicates frozen holdout")
        length = token_count(tokenizer, row)
        if length <= args.cap:
            kept.append(row)
            lengths.append(length)
    for line_no, row in enumerate(holdout, 1):
        check_trajectory(row, f"{args.holdout}:{line_no}")
        length = token_count(tokenizer, row)
        if length <= args.cap:
            kept_holdout.append(row)
            holdout_lengths.append(length)
    if not kept:
        raise SystemExit("cap rejected every record")
    if not kept_holdout:
        raise SystemExit("cap rejected every frozen holdout record")
    for line_no, row in enumerate(kept, 1):
        check_trajectory(row, f"derived:{line_no}")
    output, holdout_output = rows_text(kept), rows_text(kept_holdout)
    if {fingerprint(row) for row in kept} & {fingerprint(row) for row in kept_holdout}:
        raise SystemExit("derived train/holdout overlap")
    report = manifest(
        args.train, args.holdout, kept, kept_holdout, len(source), len(holdout), args.cap,
        args.tokenizer, template, lengths, holdout_lengths, output, holdout_output,
    )
    report_text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.out.is_file() or not args.holdout_out.is_file() or not args.manifest.is_file():
            raise SystemExit("derived output or manifest missing; run builder first")
        if args.out.read_text(encoding="utf-8") != output:
            raise SystemExit("derived JSONL differs from deterministic rebuild")
        if args.holdout_out.read_text(encoding="utf-8") != holdout_output:
            raise SystemExit("derived holdout differs from deterministic rebuild")
        if args.manifest.read_text(encoding="utf-8") != report_text:
            raise SystemExit("derived manifest differs from deterministic rebuild")
        print(f"check ok: train {len(kept)}/{len(source)}, holdout {len(kept_holdout)}/{len(holdout)} whole records; {min(lengths)}-{max(lengths)} / {min(holdout_lengths)}-{max(holdout_lengths)} tokens")
        return
    atomic_write(args.out, output)
    atomic_write(args.holdout_out, holdout_output)
    atomic_write(args.manifest, report_text)
    print(f"wrote {args.out}: {len(kept)}/{len(source)} whole records, {min(lengths)}-{max(lengths)} tokens")
    print(f"wrote {args.holdout_out}: {len(kept_holdout)}/{len(holdout)} whole records, {min(holdout_lengths)}-{max(holdout_lengths)} tokens")
    print(f"wrote {args.manifest}: dropped {len(source) - len(kept)} train and {len(holdout) - len(kept_holdout)} holdout records over cap {args.cap}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
