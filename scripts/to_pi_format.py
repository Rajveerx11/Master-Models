"""Convert generated trajectories from our authoring schema to pi's real tool schema.

Usage: python scripts/to_pi_format.py <in.jsonl> <out.jsonl>

Why: the dataset was authored with read_file/write_file/edit_file, but pi
(the serving harness behind Neura) exposes read/write/edit, and its `edit` takes
an ARRAY of {oldText,newText} rather than one old_string/new_string pair. Serving
a model trained on the authoring names into pi would fail every edit call.
Source of truth: @earendil-works/pi-coding-agent/dist/core/tools/*.js.

Renames only structured fields (tool_calls[].name, tool-result .name) and the
system line. Prose is never touched.
"""
import json
import sys

RENAME = {"read_file": "read", "write_file": "write", "edit_file": "edit"}
OLD_SYSTEM = "You are a coding agent with tools: read_file, write_file, edit_file, bash, grep."
PI_TOOLS = {"read", "write", "edit", "bash", "grep"}

# Training system prompt. Mirrors the STABLE core of pi's real system prompt
# (dist/core/system-prompt.js): the opening line, the Available-tools block built
# from each tool's promptSnippet, and the guidelines from each tool's
# promptGuidelines plus pi's two always-on ones.
#
# Deliberately EXCLUDES the volatile parts pi appends at runtime: machine-specific
# pi-doc absolute paths, project context files (CLAUDE.md/AGENTS.md of whatever repo
# is open), the user's skills catalog, Neura's persona/memory injection, and cwd.
# Those change every session; training on a snapshot of them would bake one machine's
# state into the weights. They are context, not signal -- and train-on-responses-only
# masks the system message anyway, so the only thing that must match is the tool
# contract the model has to emit against.
NEW_SYSTEM = """You are an expert coding assistant operating inside pi, a coding agent harness. You help users by reading files, executing commands, editing code, and writing new files.

Available tools:
- read: Read file contents
- bash: Execute bash commands (ls, grep, find, etc.)
- edit: Make precise file edits with exact text replacement, including multiple disjoint edits in one call
- write: Create or overwrite files
- grep: Search file contents for patterns (respects .gitignore)

Guidelines:
- Use read to examine files instead of cat or sed.
- Use edit for precise changes (edits[].oldText must match exactly)
- When changing multiple separate locations in one file, use one edit call with multiple entries in edits[] instead of multiple edit calls
- Each edits[].oldText is matched against the original file, not after earlier edits are applied. Do not emit overlapping or nested edits. Merge nearby changes into one edit.
- Keep edits[].oldText as small as possible while still being unique in the file. Do not pad with large unchanged regions.
- Use write only for new files or complete rewrites.
- Be concise in your responses
- Show file paths clearly when working with files"""


def convert_args(name, args):
    """Normalize to pi's real parameter names.

    Generators drifted on argument keys and the validator never checked them, so
    the corpus contains edit old/new AND old_string/new_string, read
    start_line/end_line AND offset/limit, grep after_context AND context_lines.
    Every observed variant is mapped here; anything unknown raises rather than
    silently shipping an argument pi will ignore.
    """
    a = dict(args)
    if name == "edit":
        if "edits" in a:  # already converted
            return a
        old = a.pop("old_string", None) or a.pop("old", None)
        new = a.pop("new_string", None) if "new_string" in a else a.pop("new", None)
        out = {"path": a.pop("path"), "edits": [{"oldText": old, "newText": new}]}
        if a:
            raise ValueError(f"unexpected edit args: {sorted(a)}")
        return out
    if name == "read":
        out = {"path": a.pop("path")}
        if "offset" in a:
            out["offset"] = a.pop("offset")
        if "limit" in a:
            out["limit"] = a.pop("limit")
        if "start_line" in a:  # inclusive line range -> pi's offset/limit
            start = a.pop("start_line")
            out["offset"] = start
            if "end_line" in a:
                out["limit"] = a.pop("end_line") - start + 1
        a.pop("end_line", None)
        if a:
            raise ValueError(f"unexpected read args: {sorted(a)}")
        return out
    if name == "grep":
        for alias in ("after_context", "context_lines", "before_context"):
            if alias in a:
                a["context"] = a.pop(alias)
        unknown = set(a) - {"pattern", "path", "glob", "ignoreCase", "literal", "context", "limit"}
        if unknown:
            raise ValueError(f"unexpected grep args: {sorted(unknown)}")
        return a
    if name == "write":
        if set(a) != {"path", "content"}:
            raise ValueError(f"unexpected write args: {sorted(a)}")
        return a
    if name == "bash":
        unknown = set(a) - {"command", "timeout"}
        if unknown:
            raise ValueError(f"unexpected bash args: {sorted(unknown)}")
        return a
    raise ValueError(f"unknown tool {name!r}")


def convert(traj):
    msgs = traj["messages"]
    if msgs[0].get("role") == "system" and msgs[0].get("content") == OLD_SYSTEM:
        msgs[0]["content"] = NEW_SYSTEM
    for m in msgs:
        for tc in m.get("tool_calls") or []:
            tc["name"] = RENAME.get(tc["name"], tc["name"])
            tc["arguments"] = convert_args(tc["name"], tc["arguments"])
        if m.get("role") == "tool" and "name" in m:
            m["name"] = RENAME.get(m["name"], m["name"])
    return traj


def verify(traj, where):
    """Fail loudly rather than ship a half-converted file."""
    msgs = traj["messages"]
    assert msgs[0]["content"] == NEW_SYSTEM, f"{where}: system line not converted"
    for i, m in enumerate(msgs):
        for tc in m.get("tool_calls") or []:
            assert tc["name"] in PI_TOOLS, f"{where}: msg {i} unknown tool {tc['name']!r}"
            a = tc["arguments"]
            if tc["name"] == "edit":
                assert isinstance(a.get("edits"), list) and a["edits"], f"{where}: msg {i} edit missing edits[]"
                for e in a["edits"]:
                    assert set(e) == {"oldText", "newText"}, f"{where}: msg {i} bad edit entry {sorted(e)}"
            assert "old_string" not in a and "new_string" not in a, f"{where}: msg {i} stale edit args"
        if m.get("role") == "tool":
            assert m.get("name") in PI_TOOLS, f"{where}: msg {i} tool result name {m.get('name')!r}"


def main(src, dst):
    n = edits = 0
    with open(dst, "w", encoding="utf-8", newline="\n") as out:
        for ln, line in enumerate(open(src, encoding="utf-8"), 1):
            if not line.strip():
                continue
            traj = convert(json.loads(line))
            verify(traj, f"{src}:{ln}")
            edits += sum(1 for m in traj["messages"] for tc in (m.get("tool_calls") or []) if tc["name"] == "edit")
            out.write(json.dumps(traj, ensure_ascii=False) + "\n")
            n += 1
    print(f"converted {n} trajectories -> {dst} ({edits} edit calls restructured)")


def demo():
    """ponytail: one runnable check. Fails if the edit restructure ever breaks."""
    t = {"messages": [
        {"role": "system", "content": OLD_SYSTEM},
        {"role": "user", "content": "x"},
        {"role": "assistant", "tool_calls": [{"name": "edit_file", "arguments": {
            "path": "a.tsx", "old_string": "foo", "new_string": "bar"}}]},
        {"role": "tool", "name": "edit_file", "content": "ok"},
        {"role": "assistant", "content": "done"}]}
    c = convert(json.loads(json.dumps(t)))
    verify(c, "demo")
    tc = c["messages"][2]["tool_calls"][0]
    assert tc["name"] == "edit"
    assert tc["arguments"] == {"path": "a.tsx", "edits": [{"oldText": "foo", "newText": "bar"}]}
    assert c["messages"][3]["name"] == "edit"
    assert c["messages"][0]["content"] == NEW_SYSTEM
    # the variant arg spellings actually present in the corpus
    assert convert_args("edit", {"path": "p", "old": "a", "new": "b"}) == {
        "path": "p", "edits": [{"oldText": "a", "newText": "b"}]}
    assert convert_args("read", {"path": "p", "start_line": 10, "end_line": 24}) == {
        "path": "p", "offset": 10, "limit": 15}
    assert convert_args("read", {"path": "p", "offset": 5, "limit": 20}) == {
        "path": "p", "offset": 5, "limit": 20}
    assert convert_args("grep", {"pattern": "x", "path": "s", "after_context": 3}) == {
        "pattern": "x", "path": "s", "context": 3}
    for bad in [("edit", {"path": "p", "old": "a", "new": "b", "junk": 1}),
                ("bash", {"command": "x", "shell": "zsh"})]:
        try:
            convert_args(*bad)
            raise AssertionError(f"should have rejected {bad}")
        except ValueError:
            pass
    print("demo ok")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--demo":
        demo()
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
