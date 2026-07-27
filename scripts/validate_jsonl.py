"""Validate generated trajectory JSONL: schema, tool discipline, dedup, stats.

Usage: python scripts/validate_jsonl.py <file-or-glob> [more...]
Exit 1 on any hard schema failure. Warnings don't fail.
"""
import glob
import json
import sys
from difflib import SequenceMatcher

TOOLS = {"read_file", "write_file", "edit_file", "bash", "grep"}
SYSTEM = "You are a coding agent with tools: read_file, write_file, edit_file, bash, grep."


def check(traj, where):
    errs, warns = [], []
    m = traj.get("messages")
    if not isinstance(m, list) or len(m) < 4:
        return [f"{where}: messages missing/too short"], warns, 0
    if m[0].get("role") != "system" or m[0].get("content") != SYSTEM:
        errs.append(f"{where}: bad system message")
    if m[1].get("role") != "user" or not m[1].get("content", "").strip():
        errs.append(f"{where}: bad user message")
    tool_turns = 0
    for i, msg in enumerate(m[2:], start=2):
        role = msg.get("role")
        if role == "assistant" and "tool_calls" in msg:
            tool_turns += 1
            for tc in msg["tool_calls"]:
                if tc.get("name") not in TOOLS:
                    errs.append(f"{where}: unknown tool {tc.get('name')!r}")
                if not isinstance(tc.get("arguments"), dict):
                    errs.append(f"{where}: msg {i} arguments not an object")
            nxt = m[i + 1] if i + 1 < len(m) else {}
            if nxt.get("role") != "tool" or nxt.get("name") != msg["tool_calls"][0].get("name"):
                errs.append(f"{where}: msg {i} tool_call not followed by matching tool result")
        elif role not in ("assistant", "tool"):
            errs.append(f"{where}: msg {i} unexpected role {role!r}")
    last = m[-1]
    if last.get("role") != "assistant" or not last.get("content") or "tool_calls" in last:
        errs.append(f"{where}: last message must be assistant summary")
    if tool_turns == 0:
        errs.append(f"{where}: no tool use")
    elif not 3 <= tool_turns <= 8:
        warns.append(f"{where}: {tool_turns} tool turns (expected 3-8)")
    return errs, warns, tool_turns


def main(patterns):
    files = sorted(f for p in patterns for f in glob.glob(p))
    if not files:
        sys.exit("no files matched")
    errs, warns, tasks, turn_counts, recoveries = [], [], [], [], 0
    for f in files:
        for n, line in enumerate(open(f, encoding="utf-8"), 1):
            if not line.strip():
                continue
            where = f"{f}:{n}"
            try:
                traj = json.loads(line)
            except json.JSONDecodeError as e:
                errs.append(f"{where}: invalid JSON ({e})")
                continue
            e, w, t = check(traj, where)
            errs += e
            warns += w
            turn_counts.append(t)
            tasks.append((where, traj["messages"][1].get("content", "") if traj.get("messages") and len(traj["messages"]) > 1 else ""))
            joined = " ".join(str(m.get("content", "")) for m in traj["messages"] if m.get("role") == "tool")
            if "error" in joined.lower() or "not found" in joined.lower() or "no matches" in joined.lower():
                recoveries += 1
    # ponytail: pairwise SequenceMatcher fine at batch scale; swap for ROUGE-L dedup at 5-10K
    for i in range(len(tasks)):
        for j in range(i + 1, len(tasks)):
            r = SequenceMatcher(None, tasks[i][1].lower(), tasks[j][1].lower()).ratio()
            if r > 0.8:
                warns.append(f"near-duplicate tasks ({r:.2f}): {tasks[i][0]} vs {tasks[j][0]}")
    print(f"{len(tasks)} trajectories in {len(files)} file(s); "
          f"tool turns min/avg/max = {min(turn_counts)}/{sum(turn_counts)/len(turn_counts):.1f}/{max(turn_counts)}; "
          f"{recoveries} contain an error/recovery signal")
    for w in warns:
        print("WARN", w)
    for e in errs:
        print("FAIL", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main(sys.argv[1:] or ["datasets/*/generated/raw/*.jsonl"])
