"""Assemble datasets/frontend-stack/final/{train,holdout}.jsonl.

Mix (v1, decided in plan/v1-release-plan.md Phase 2 step 7):
    242 domain (60%) + 81 general tool-calling (20%) + 81 general instruction (20%)
    = 404 records, 5% stratified holdout for loss tracking only.

Every record is `{"messages": [...], "tools": [...], "source": "..."}`.
`tools` is pi's real tool array (training/pi_tools.json) for domain records and the
example's own tools for general tool-calling records. Dolly records carry no tools,
which is deliberate: they preserve plain-chat ability.

Why tool_calls stay flat ({"name", "arguments"}) instead of OpenAI's nested
{"id","type","function":{...}}: the Qwen3 template unwraps `.function` if present and
otherwise reads `.name`/`.arguments` directly, and it ignores `id` / `tool_call_id`
entirely. Both shapes render byte-identical -- asserted in demo(). The flat shape is
what the corpus already uses, so restructuring it would be churn with no effect on the
text the model actually trains on.

    python scripts/build_train_mix.py          # build
    python scripts/build_train_mix.py --demo   # self-check, writes nothing
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = ROOT / "datasets/frontend-stack/filtered/keep_ge7.pi.jsonl"
HERMES = ROOT / "datasets/general/raw/hermes-func-calling.json"
DOLLY = ROOT / "datasets/general/raw/dolly-15k.jsonl"
PI_TOOLS = ROOT / "training/pi_tools.json"
TEMPLATE = ROOT / "training/templates/qwen3-8b.jinja"
OUT_DIR = ROOT / "datasets/frontend-stack/final"

SEED = 731  # same seed as the keep-set spot-check
N_TOOLCALL = 81
N_GENERAL = 81
HOLDOUT_FRAC = 0.05

# pi presents seven tools; the corpus system prompt only listed the five it uses.
# find/ls are appended so the trained prompt matches the served one. Snippets are the
# first sentence of pi's own tool descriptions, not invented copy.
EXTRA_TOOL_LINES = (
    "- grep: Search file contents for patterns (respects .gitignore)\n"
    "- find: Find files and directories by glob pattern\n"
    "- ls: List directory contents"
)

TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)
TOOL_RESP_RE = re.compile(r"<tool_response>\s*(\{.*?\})\s*</tool_response>", re.S)


# Public sources, licence-checked 2026-07-31 via the HF datasets API. Both are
# downloaded on demand; datasets/general/raw/ is gitignored (33 MB, re-fetchable).
SOURCES = {
    HERMES: ("https://huggingface.co/datasets/NousResearch/hermes-function-calling-v1"
             "/resolve/main/func-calling.json", "Apache-2.0"),
    DOLLY: ("https://huggingface.co/datasets/databricks/databricks-dolly-15k"
            "/resolve/main/databricks-dolly-15k.jsonl", "CC-BY-SA-3.0"),
}


def fetch_missing() -> None:
    import urllib.request

    for dst, (url, lic) in SOURCES.items():
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        print(f"  downloading {dst.name} ({lic})...")
        urllib.request.urlretrieve(url, dst)


def load_pi_tools() -> list[dict]:
    tools = json.loads(PI_TOOLS.read_text(encoding="utf-8"))
    names = [t["function"]["name"] for t in tools]
    if sorted(names) != sorted(["read", "bash", "edit", "write", "grep", "find", "ls"]):
        raise SystemExit(f"pi_tools.json has unexpected tools: {names}. Re-run dump_pi_tools.mjs.")
    return tools


def patch_system(text: str) -> str:
    """Extend the corpus tool list to pi's full seven-tool surface."""
    old = "- grep: Search file contents for patterns (respects .gitignore)"
    if old not in text:
        raise SystemExit("system prompt changed shape; update EXTRA_TOOL_LINES")
    return text.replace(old, EXTRA_TOOL_LINES, 1)


def build_domain(tools: list[dict]) -> list[dict]:
    out = []
    for line in DOMAIN.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        msgs = rec["messages"]
        if msgs[0]["role"] != "system":
            raise SystemExit("domain record missing leading system message")
        msgs[0] = {**msgs[0], "content": patch_system(msgs[0]["content"])}
        out.append({"messages": msgs, "tools": tools, "source": "frontend-stack"})
    return out


def convert_hermes(rec: dict) -> dict | None:
    """Re-shape one Hermes record into structured tool_calls.

    Hermes encodes calls as <tool_call> XML inside message text and ships its own
    <tools> system prompt. Training on that raw teaches a competing syntax, so the
    tools move to the `tools` field and the calls become real tool_calls; the Qwen3
    template then renders them in the one format the server parses.
    """
    try:
        tools = json.loads(rec["tools"]) if isinstance(rec.get("tools"), str) else rec.get("tools")
    except json.JSONDecodeError:
        return None
    if not isinstance(tools, list) or not tools:
        return None

    msgs: list[dict] = []
    for turn in rec.get("conversations", []):
        who, val = turn.get("from"), turn.get("value") or ""
        if who == "system":
            continue  # its tool block is replaced by the `tools` field
        if who == "human":
            msgs.append({"role": "user", "content": val})
        elif who == "gpt":
            calls = []
            for raw in TOOL_CALL_RE.findall(val):
                try:
                    c = json.loads(raw)
                except json.JSONDecodeError:
                    return None  # drop the whole record rather than lose a call
                if "name" not in c:
                    return None
                calls.append({"name": c["name"], "arguments": c.get("arguments", {})})
            text = TOOL_CALL_RE.sub("", val).strip()
            if calls:
                m = {"role": "assistant", "tool_calls": calls}
                if text:
                    m["content"] = text
                msgs.append(m)
            elif text:
                msgs.append({"role": "assistant", "content": text})
        elif who == "tool":
            bodies = TOOL_RESP_RE.findall(val)
            if not bodies:
                return None
            for raw in bodies:
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    return None
                inner = obj.get("content", obj) if isinstance(obj, dict) else obj
                msgs.append({
                    "role": "tool",
                    "name": obj.get("name", "") if isinstance(obj, dict) else "",
                    "content": inner if isinstance(inner, str) else json.dumps(inner),
                })
        else:
            return None

    if not any(m["role"] == "assistant" and m.get("tool_calls") for m in msgs):
        return None
    if not msgs or msgs[0]["role"] != "user" or msgs[-1]["role"] != "assistant":
        return None
    return {"messages": msgs, "tools": tools, "source": "hermes-function-calling-v1"}


def build_toolcalling(n: int, rng: random.Random) -> list[dict]:
    raw = json.loads(HERMES.read_text(encoding="utf-8"))
    order = list(range(len(raw)))
    rng.shuffle(order)
    out, dropped = [], 0
    for i in order:
        if len(out) >= n:
            break
        c = convert_hermes(raw[i])
        if c is None:
            dropped += 1
        else:
            out.append(c)
    print(f"  hermes: kept {len(out)}, skipped {dropped} unparseable of {len(order)} scanned")
    if len(out) < n:
        raise SystemExit(f"only {len(out)}/{n} hermes records converted")
    return out


def build_general(n: int, rng: random.Random) -> list[dict]:
    rows = [json.loads(l) for l in DOLLY.read_text(encoding="utf-8").splitlines() if l.strip()]
    # closed-QA/summarisation entries carry a long `context`; keep the mix readable by
    # sampling across categories rather than whatever the head of the file happens to be.
    rng.shuffle(rows)
    out = []
    for r in rows:
        if len(out) >= n:
            break
        instr, ctx, resp = r.get("instruction", ""), r.get("context", ""), r.get("response", "")
        if not instr.strip() or not resp.strip():
            continue
        user = f"{instr}\n\n{ctx}".strip() if ctx.strip() else instr
        out.append({
            "messages": [{"role": "user", "content": user},
                         {"role": "assistant", "content": resp}],
            "source": "databricks-dolly-15k",
        })
    if len(out) < n:
        raise SystemExit(f"only {len(out)}/{n} dolly records usable")
    return out


def stratified_split(groups: dict[str, list[dict]], frac: float, rng: random.Random):
    """Hold out `frac` of EACH source, so the holdout is not accidentally all one kind."""
    train, hold = [], []
    for name, rows in groups.items():
        rows = rows[:]
        rng.shuffle(rows)
        k = max(1, round(len(rows) * frac))
        hold += rows[:k]
        train += rows[k:]
    rng.shuffle(train)
    rng.shuffle(hold)
    return train, hold


def render(messages, tools=None) -> str:
    from jinja2 import Environment

    env = Environment(trim_blocks=False, lstrip_blocks=False)
    env.policies["json.dumps_kwargs"] = {"ensure_ascii": False}
    tpl = env.from_string(TEMPLATE.read_text(encoding="utf-8"))
    return tpl.render(messages=messages, tools=tools, add_generation_prompt=False)


def demo() -> None:
    """Assertions that fail if the shape decisions above stop holding."""
    flat = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "tool_calls": [{"name": "read", "arguments": {"path": "a.ts"}}]},
        {"role": "tool", "name": "read", "content": "file body"},
        {"role": "assistant", "content": "done"},
    ]
    nested = json.loads(json.dumps(flat))
    nested[2]["tool_calls"] = [{
        "id": "call_0", "type": "function",
        "function": {"name": "read", "arguments": {"path": "a.ts"}},
    }]
    nested[3]["tool_call_id"] = "call_0"
    tools = load_pi_tools()

    a, b = render(flat, tools), render(nested, tools)
    assert a == b, "flat and OpenAI-nested tool_calls no longer render identically"
    assert "<tool_call>\n{\"name\": \"read\", \"arguments\": {\"path\": \"a.ts\"}}" in a, a[-400:]
    assert "<tool_response>\nfile body\n</tool_response>" in a
    # tools present => the template emits the <tools> block; absent => plain system line
    assert "<tools>" in a and "<tools>" not in render(flat, None)

    # Hermes conversion must leave no raw XML markers behind.
    rec = {
        "tools": json.dumps([{"type": "function", "function": {"name": "get_x", "parameters": {}}}]),
        "conversations": [
            {"from": "system", "value": "<tools>[...]</tools>"},
            {"from": "human", "value": "do it"},
            {"from": "gpt", "value": '<tool_call>\n{"name": "get_x", "arguments": {"a": 1}}\n</tool_call>'},
            {"from": "tool", "value": '<tool_response>\n{"name": "get_x", "content": {"ok": true}}\n</tool_response>'},
            {"from": "gpt", "value": "all set"},
        ],
    }
    c = convert_hermes(rec)
    assert c and c["messages"][1]["tool_calls"][0]["arguments"] == {"a": 1}
    assert not any(t in json.dumps(c) for t in ("<tool_call>", "<tool_response>", "</tools>"))
    assert convert_hermes({**rec, "conversations": rec["conversations"][:2]}) is None

    assert patch_system("- grep: Search file contents for patterns (respects .gitignore)").endswith("- ls: List directory contents")

    g = {"a": [{"i": i} for i in range(20)], "b": [{"i": i} for i in range(20)]}
    tr, ho = stratified_split(g, 0.05, random.Random(0))
    assert len(ho) == 2 and len(tr) == 38, (len(tr), len(ho))
    print("demo ok")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()

    rng = random.Random(SEED)
    tools = load_pi_tools()
    print("building mix...")
    fetch_missing()
    groups = {
        "frontend-stack": build_domain(tools),
        "hermes": build_toolcalling(N_TOOLCALL, rng),
        "dolly": build_general(N_GENERAL, rng),
    }
    for k, v in groups.items():
        print(f"  {k}: {len(v)}")

    train, hold = stratified_split(groups, HOLDOUT_FRAC, rng)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in (("train", train), ("holdout", hold)):
        p = OUT_DIR / f"{name}.jsonl"
        with p.open("w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"wrote {p} ({len(rows)} records)")

    # Render every record once: a template failure must surface here, not mid-training.
    for r in train + hold:
        txt = render(r["messages"], r.get("tools"))
        if "<tool_call>" in json.dumps(r["messages"]) :
            raise SystemExit(f"raw <tool_call> text leaked into {r['source']}")
        if not txt.strip():
            raise SystemExit(f"empty render for a {r['source']} record")
    print("all records render cleanly through the Qwen3 template")

    total = len(train) + len(hold)
    print(f"total {total}  train {len(train)}  holdout {len(hold)}")


if __name__ == "__main__":
    sys.exit(main())
