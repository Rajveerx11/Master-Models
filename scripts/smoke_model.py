"""Ten cheap post-export checks for tool syntax and catastrophic forgetting."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = json.loads((ROOT / "training/pi_tools.json").read_text(encoding="utf-8"))
SYSTEM = (
    "You are an expert coding assistant operating inside pi. Read before editing, "
    "use only provided tools, keep changes precise, and verify changed code."
)
TOOL_NAMES = {tool["function"]["name"] for tool in TOOLS}


def request(api: str, messages: list[dict], tools: bool) -> dict:
    body = {
        "model": "local",
        "messages": messages,
        "temperature": 0,
        "max_tokens": 700,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if tools:
        body["tools"] = TOOLS
    req = urllib.request.Request(
        api.rstrip("/") + "/v1/chat/completions",
        json.dumps(body).encode("utf-8"),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as response:
        message = json.load(response)["choices"][0]["message"]
    calls = []
    for call in message.get("tool_calls") or []:
        function = call.get("function", call)
        arguments = function.get("arguments", {})
        valid = True
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                valid = False
        calls.append({"name": function.get("name"), "arguments": arguments, "valid": valid})
    return {"content": message.get("content") or "", "tool_calls": calls}


def cases():
    user = lambda content: {"role": "user", "content": content}
    return [
        ("read_first", True, [user("Fix the disabled SaveButton in src/SaveButton.tsx.")],
         lambda r: bool(r["tool_calls"]) and r["tool_calls"][0]["name"] in {"read", "grep"}),
        ("pi_edit_schema", True, [
            user("In src/a.ts replace `const x = 1` with `const x = 2`."),
            {"role": "assistant", "tool_calls": [{"name": "read", "arguments": {"path": "src/a.ts"}}]},
            {"role": "tool", "name": "read", "content": "const x = 1"},
        ],
         lambda r: bool(r["tool_calls"]) and r["tool_calls"][0]["name"] == "edit"
         and isinstance(r["tool_calls"][0]["arguments"].get("edits"), list)),
        ("valid_tool_json", True, [user('Search src for the exact text `Say "hello"`.')],
         lambda r: bool(r["tool_calls"]) and all(call["valid"] for call in r["tool_calls"])),
        ("no_unknown_tool", True, [user("Use the deploy tool to release this project.")],
         lambda r: all(call["name"] in TOOL_NAMES for call in r["tool_calls"])),
        ("recover_after_missing_file", True, [
            user("Fix src/missing.ts"),
            {"role": "assistant", "tool_calls": [{"name": "read", "arguments": {"path": "src/missing.ts"}}]},
            {"role": "tool", "name": "read", "content": "Error: file not found"},
        ], lambda r: bool(r["tool_calls"]) and r["tool_calls"][0]["name"] in {"grep", "find", "ls"}),
        ("empty_file_action", True, [
            user("Add `export const ready = true` to src/empty.ts"),
            {"role": "assistant", "tool_calls": [{"name": "read", "arguments": {"path": "src/empty.ts"}}]},
            {"role": "tool", "name": "read", "content": ""},
        ], lambda r: bool(r["tool_calls"]) and r["tool_calls"][0]["name"] in {"write", "edit"}),
        ("general_math", False, [user("What is 17 multiplied by 19? Answer with the number only.")],
         lambda r: r["content"].strip() == "323"),
        ("general_knowledge", False, [user("What is the capital of France? Answer briefly.")],
         lambda r: "paris" in r["content"].lower()),
        ("json_discipline", False, [user('Return only JSON: {"ok": true, "count": 2}')],
         lambda r: _is_expected_json(r["content"])),
        ("general_explanation", False, [user("Explain database connection pooling in one sentence.")],
         lambda r: "connection" in r["content"].lower() and len(r["content"].split()) < 60),
    ]


def _is_expected_json(text: str) -> bool:
    try:
        return json.loads(text.strip()) == {"ok": True, "count": 2}
    except json.JSONDecodeError:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8080")
    ap.add_argument("--output", type=Path, default=ROOT / "outputs/frontend-stack/smoke.jsonl")
    args = ap.parse_args()
    results = []
    for name, use_tools, extra, check in cases():
        started = time.time()
        try:
            response = request(args.api, [{"role": "system", "content": SYSTEM}, *extra], use_tools)
            passed = bool(check(response))
            error = None
        except Exception as exc:
            response, passed, error = {"content": "", "tool_calls": []}, False, str(exc)
        record = {
            "case": name,
            "pass": passed,
            "latency_s": round(time.time() - started, 2),
            "error": error,
            "response": response,
        }
        results.append(record)
        print(f"[{'PASS' if passed else 'FAIL'}] {name} ({record['latency_s']}s)")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in results:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    passed = sum(record["pass"] for record in results)
    print(f"{passed}/{len(results)} passed -> {args.output}")
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
