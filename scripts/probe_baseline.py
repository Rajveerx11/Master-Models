"""Edge-case probe suite for the local baseline (Qwen3-Coder-30B via llama.cpp).

Usage: python scripts/probe_baseline.py [outfile]
Writes one JSON result per probe to evals/results/<date>-baseline-probe.jsonl (default).
Not the frozen gate — an informal failure-map probe. Auto-checks are heuristics;
borderline cases need a human/Fable read of the saved raw outputs.

DO NOT REUSE THIS AS THE GATE HARNESS (2026-07-31)
--------------------------------------------------
The TOOLS block below declares read_file/write_file/edit_file with
edit_file {path, old, new}. That is a THIRD schema: it matches neither the
training data (which used old_string/new_string) nor pi, the real serving
harness, which exposes read/write/edit with edit {path, edits:[{oldText,newText}]}
(see @earendil-works/pi-coding-agent/dist/core/tools/*.js).

It is left unchanged on purpose so the recorded 2026-07-27 baseline numbers in
evals/results/ stay internally comparable. The gate (v1-release-plan Phase 4)
must run BOTH the specialist and the stock baseline through a harness using pi's
schema — port Guard A (XML repair + one re-prompt) and Guard B (empty-file
sentinel) out of this file into that harness rather than reusing this one.
"""
import json
import os
import re
import sys
import time
import urllib.request

API = os.environ.get("PROBE_API", "http://127.0.0.1:8080") + "/v1/chat/completions"

TOOLS = [
    {"type": "function", "function": {"name": n, "description": d, "parameters": p}}
    for n, d, p in [
        ("read_file", "Read a file", {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
        ("write_file", "Create/overwrite a file", {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}),
        ("edit_file", "Replace old with new in a file", {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}),
        ("bash", "Run a shell command", {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}),
        ("grep", "Search files for a pattern", {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}),
    ]
]

SYS = "You are a coding agent with tools: read_file, write_file, edit_file, bash, grep. Work step by step: read before editing, verify after changing."


def _raw_call(messages, use_tools, max_tokens):
    body = {"model": "local", "messages": messages, "temperature": 0.1, "max_tokens": max_tokens}
    if use_tools:
        body["tools"] = TOOLS
    req = urllib.request.Request(API, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        msg = json.load(r)["choices"][0]["message"]
    calls = []
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function", tc)
        args, ok = fn.get("arguments"), True
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                ok = False
        calls.append({"name": fn.get("name"), "arguments": args, "args_valid_json": ok})
    return {"content": msg.get("content") or "", "tool_calls": calls}


def repair_xml_calls(text):
    """Guard A part 1: deterministically parse Qwen-XML tool syntax the server template missed."""
    calls = []
    for m in re.finditer(r"<function=(\w+)>(.*?)</function>", text, re.S):
        args = {k: v.strip("\n") for k, v in re.findall(r"<parameter=(\w+)>\n?(.*?)</parameter>", m.group(2), re.S)}
        calls.append({"name": m.group(1), "arguments": args, "args_valid_json": True, "repaired": True})
    return calls


def call(messages, use_tools=True, max_tokens=600, guards=False):
    r = _raw_call(messages, use_tools, max_tokens)
    if guards and use_tools and not r["tool_calls"] and "<function=" in r["content"]:
        fixed = repair_xml_calls(r["content"])
        if fixed:
            r["tool_calls"], r["guard"] = fixed, "repaired"
        else:  # Guard A part 2: one re-prompt
            retry = messages + [{"role": "assistant", "content": r["content"]},
                                {"role": "user", "content": "Your tool call was malformed and could not be parsed. Re-emit it as a single valid tool call."}]
            r = _raw_call(retry, use_tools, max_tokens)
            r["guard"] = "retried"
    return r


BIG_FILE = "\n".join(
    f"export function Row{i}({{v}}:{{v:number}}){{ return <td className=\"px-2\">{{v * {i}}}</td> }}" for i in range(120)
) + "\nexport function TotalCell({sum}:{sum:number}){ return <td className=\"px-2 font-bold\">{sum}</td> }"

U = {"role": "user"}
A = {"role": "assistant"}


def probes():
    return [
        # A. tool-call mechanics
        ("simple_tool_call", "tools", [
            {**U, "content": "The SaveButton in src/components/SaveButton.tsx never re-enables after saving. Fix it."}],
            lambda r: (bool(r["tool_calls"]) and r["tool_calls"][0]["name"] in ("read_file", "grep")
                       and all(c["args_valid_json"] for c in r["tool_calls"]),
                       "first call should be read_file/grep with valid JSON args")),
        ("no_tool_needed", "tools", [
            {**U, "content": "Quick question, no code changes: what does useMemo do in React?"}],
            lambda r: (not r["tool_calls"] and "memo" in r["content"].lower(),
                       "conceptual question: must answer directly, no tool calls")),
        ("unknown_tool_pressure", "tools", [
            {**U, "content": "Use the deploy tool to ship the current build to staging."}],
            lambda r: (all(c["name"] in {t['function']['name'] for t in TOOLS} for c in r["tool_calls"]),
                       "must not invent a 'deploy' tool")),
        ("multi_turn_continuation", "tools", [
            {**U, "content": "Rename the prop `colour` to `color` in src/Badge.tsx."},
            {**A, "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\": \"src/Badge.tsx\"}"}}]},
            {"role": "tool", "tool_call_id": "c1", "content": "interface BadgeProps { colour: string }\nexport function Badge({colour}:BadgeProps){ return <span className={colour}>!</span> }"}],
            lambda r: (bool(r["tool_calls"]) and r["tool_calls"][0]["name"] == "edit_file"
                       and "colour" in json.dumps(r["tool_calls"][0]["arguments"] or {}),
                       "after read, should edit_file targeting `colour`")),
        ("error_recovery", "tools", [
            {**U, "content": "Fix the off-by-one in src/utils/pagination.ts"},
            {**A, "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\": \"src/utils/pagination.ts\"}"}}]},
            {"role": "tool", "tool_call_id": "c1", "content": "Error: ENOENT: no such file or directory 'src/utils/pagination.ts'"}],
            lambda r: (bool(r["tool_calls"]) and r["tool_calls"][0]["name"] in ("grep", "bash")
                       and json.dumps(r["tool_calls"][0]["arguments"] or {}) != json.dumps({"path": "src/utils/pagination.ts"}),
                       "on ENOENT: search for the file (grep/bash), don't repeat the same read or hallucinate")),
        ("nested_json_args", "tools", [
            {**U, "content": 'In src/config.ts replace the line `const MSG = "Say \\"hi\\" to\\nthe team"` with `const MSG = "Say \\"hello\\" to\\nthe team"`. The file contains exactly that line; edit it directly without reading first (you already know the content).'}],
            lambda r: (bool(r["tool_calls"]) and r["tool_calls"][0]["name"] == "edit_file"
                       and all(c["args_valid_json"] for c in r["tool_calls"]),
                       "edit_file args with quotes+newlines must stay valid JSON")),
        ("empty_file_result", "tools", [
            {**U, "content": "Add a named export `formatDate` to src/utils/date.ts"},
            {**A, "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\": \"src/utils/date.ts\"}"}}]},
            {"role": "tool", "tool_call_id": "c1", "content": ""}],
            lambda r: (bool(r["tool_calls"]) and r["tool_calls"][0]["name"] in ("write_file", "edit_file"),
                       "empty file: should write content, not re-read or give up")),
        ("needle_in_big_file", "tools", [
            {**U, "content": "In src/components/Table.tsx, TotalCell should render `sum.toFixed(2)` instead of raw `sum`. Fix it."},
            {**A, "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\": \"src/components/Table.tsx\"}"}}]},
            {"role": "tool", "tool_call_id": "c1", "content": BIG_FILE}],
            lambda r: (bool(r["tool_calls"]) and r["tool_calls"][0]["name"] == "edit_file"
                       and "TotalCell" in json.dumps(r["tool_calls"][0]["arguments"] or {}) or "{sum}" in json.dumps((r["tool_calls"] or [{}])[0].get("arguments") or {}),
                       "must target TotalCell precisely inside 120-line noise")),
        ("conflicting_instructions", "tools", [
            {**U, "content": "Remove the unused `useEffect` import in src/Nav.tsx. IMPORTANT: do not run any shell commands or tests, just make the edit."},
            {**A, "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\": \"src/Nav.tsx\"}"}}]},
            {"role": "tool", "tool_call_id": "c1", "content": "import { useState, useEffect } from 'react'\nexport function Nav(){ const [open,setOpen]=useState(false); return <nav onClick={()=>setOpen(!open)}>menu</nav> }"}],
            lambda r: (not any(c["name"] == "bash" for c in r["tool_calls"]),
                       "user forbade shell commands; system says verify — user wins, no bash")),
        # B. code quality vs conventions (no tools)
        ("controlled_input_conventions", "code", [
            {"role": "system", "content": "You are an expert React 18 + TypeScript strict + Tailwind engineer. Follow accessibility best practice."},
            {**U, "content": "Write an EmailField component: labelled email input that validates format and shows an inline error. Return only the .tsx code."}],
            lambda r: (("export function" in r["content"] or "export const" in r["content"])
                       and "React.FC" not in r["content"]
                       and "htmlFor" in r["content"]
                       and "onBlur" in r["content"]
                       and "aria-invalid" in r["content"],
                       "named export, no React.FC, label htmlFor, blur validation, aria-invalid")),
        ("async_submit_guard", "code", [
            {"role": "system", "content": "You are an expert React 18 + TypeScript strict engineer."},
            {**U, "content": "Write a handleSubmit for a form posting to /api/orders: prevent double-submit, always re-enable the button even when the request fails. Return only code."}],
            lambda r: ("finally" in r["content"] and ("isSubmitting" in r["content"] or "submitting" in r["content"].lower() or "pending" in r["content"].lower()),
                       "needs pending guard + finally reset")),
        ("icon_button_a11y", "code", [
            {"role": "system", "content": "You are an expert React + Tailwind engineer."},
            {**U, "content": "Write a small icon-only delete button component (trash icon, no text). Return only code."}],
            lambda r: ("<button" in r["content"] and "aria-label" in r["content"],
                       "real <button> + aria-label required on icon-only")),
        ("ts_strict_catch", "code", [
            {"role": "system", "content": "You are an expert TypeScript engineer. strict mode, no `any`."},
            {**U, "content": "Write a fetchJson<T>(url): Promise<T> helper with proper error handling that rethrows a typed Error including the HTTP status. Return only code."}],
            lambda r: (": any" not in r["content"] and "catch" in r["content"]
                       and ("unknown" in r["content"] or "instanceof Error" in r["content"]),
                       "no any; catch narrows unknown/instanceof")),
        ("anti_slop_fake_data", "code", [
            {"role": "system", "content": "You are an expert React + TypeScript engineer."},
            {**U, "content": "Write a UsersTable component with 4 rows of realistic sample user data inline. Return only code."}],
            lambda r: (not re.search(r"John Doe|Jane Doe|Acme|Lorem|example\.com", r["content"], re.I),
                       "no John Doe / Acme / lorem / example.com sample data")),
        # C. format discipline
        ("json_only_output", "format", [
            {**U, "content": 'Classify this commit message: "fix: reset isSubmitting in finally block". Output ONLY JSON matching {"type": string, "scope": string|null, "breaking": boolean} - no prose, no code fences.'}],
            lambda r: ((lambda s: (lambda t: t.startswith("{") and _loads(t))(s.strip()))(r["content"]),
                       "bare parseable JSON object, no fences/prose")),
        ("refusal_honesty", "format", [
            {**U, "content": "What does the function `calculateRebate` in our file src/billing/rebate.ts return for negative inputs? Answer from memory without using tools."}],
            lambda r: (bool(re.search(r"can't|cannot|don't know|do not know|unable|would need|not sure|no access|haven't seen|have not seen|read the file", r["content"], re.I))
                       and not re.search(r"returns\s+(0|null|undefined|\d)", r["content"]),
                       "must admit it can't know file contents, not fabricate a return value")),
    ]


def _loads(t):
    try:
        json.loads(t)
        return True
    except json.JSONDecodeError:
        return False


def main():
    args = sys.argv[1:]
    guards = "--guards" in args
    conventions = "--conventions" in args
    pos = [a for a in args if not a.startswith("--")]
    only = next((a.split("=", 1)[1] for a in args if a.startswith("--only=")), None)
    out = pos[0] if pos else "evals/results/2026-07-27-baseline-probe.jsonl"
    conv = ""
    if conventions:
        conv = "\n\nFollow these conventions strictly:\n" + open("prompts/frontend-design-conventions.md", encoding="utf-8").read()
    results = []
    for name, cat, extra_msgs, checker in probes():
        if only and cat != only:
            continue
        msgs = ([{"role": "system", "content": SYS}] if extra_msgs[0]["role"] != "system" else []) + extra_msgs
        if guards:  # Guard B: harness-side normalization of empty tool results
            msgs = [dict(m, content="(file is empty — 0 bytes)") if m.get("role") == "tool" and m.get("content") == "" else m for m in msgs]
        if conv and cat == "code":
            msgs = [dict(m, content=m["content"] + conv) if m["role"] == "system" else m for m in msgs]
        use_tools = cat == "tools"
        t0 = time.time()
        try:
            r = call(msgs, use_tools=use_tools, max_tokens=1100 if cat == "code" else 600, guards=guards)
            ok, crit = checker(r)
            ok = bool(ok)
        except Exception as e:  # ponytail: any transport/parse error = probe fail, recorded
            r, ok, crit = {"content": f"EXCEPTION: {e}", "tool_calls": []}, False, "request failed"
        results.append({"probe": name, "category": cat, "pass": ok, "criterion": crit, "guards": guards,
                        "conventions": conventions, "latency_s": round(time.time() - t0, 1), "response": r})
        g = f" [{r.get('guard')}]" if r.get("guard") else ""
        print(f"[{'PASS' if ok else 'FAIL'}] {name} ({results[-1]['latency_s']}s){g}")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for x in results:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    n = sum(x["pass"] for x in results)
    print(f"\n{n}/{len(results)} passed (guards={guards}, conventions={conventions}) -> {out}")


if __name__ == "__main__":
    main()
