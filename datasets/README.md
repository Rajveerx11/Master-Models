# Datasets

One folder per domain, same pipeline stages inside each:

```
datasets/
  frontend-stack/
    seeds/        50-100 hand-curated gold pairs (seeds.jsonl)
    generated/    raw Fable output, per topic-matrix cell (raw/ is gitignored)
    filtered/     top ~30% after judge + spot check
    final/        source train.jsonl plus bounded train-short4096.jsonl for Unsloth
  backend-stack/
  code-review/
```

## Format — every stage, same schema

JSONL, one trajectory per line, OpenAI-style messages with tool calls:

```json
{"messages": [
  {"role": "system", "content": "You are a coding agent with tools: read_file, write_file, edit_file, bash, grep."},
  {"role": "user", "content": "The SubmitButton stays disabled after a failed request. Fix it."},
  {"role": "assistant", "tool_calls": [{"name": "grep", "arguments": {"pattern": "SubmitButton", "path": "src/"}}]},
  {"role": "tool", "name": "grep", "content": "src/components/SubmitButton.tsx:12 ..."},
  {"role": "assistant", "tool_calls": [{"name": "read_file", "arguments": {"path": "src/components/SubmitButton.tsx"}}]},
  {"role": "tool", "name": "read_file", "content": "..."},
  {"role": "assistant", "tool_calls": [{"name": "edit_file", "arguments": {"path": "src/components/SubmitButton.tsx", "old": "...", "new": "..."}}]},
  {"role": "tool", "name": "edit_file", "content": "ok"},
  {"role": "assistant", "content": "Fixed: error branch now resets `isSubmitting` in the finally block."}
]}
```

Tool names/format must match what the serving harness (pi/Hermes) emits — check
the harness's actual tool schema before generating at scale, converting later is
painful.

## Rules

- Nothing from `evals/tasks/` may appear here, ever, in any form.
- `final/train.jsonl` mix: ~60% domain / 15-20% general tool-calling / 20-30%
  general instruction (see prompts/teacher-generation-prompt.md).
- Build `final/train-short4096.jsonl` with `python scripts/build_short_train.py`
  before QLoRA on 8 GB VRAM. It filters whole rendered records at ≤4096 tokens;
  never truncate inside a message or a tool-call/result pair.
- Keep judge scores alongside filtered data (`filtered/scores.jsonl`) for later
  ablations.
