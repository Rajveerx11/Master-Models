# Datasets

Current v1 contains one completed domain: `frontend-stack`. Backend-stack and
code-review remain deferred and contain placeholders only.

## Frontend-stack pipeline

```text
datasets/frontend-stack/
  seeds/       Early pilot inputs
  generated/   Raw batch outputs; raw files stay local and are gitignored
  filtered/    Score-threshold keep set, pi-schema conversion, spot-check record
  final/       Frozen source mix, holdout, 4,096-token derivatives, manifests
```

Verified counts:

| Stage | Records | Notes |
|---|---:|---|
| Generated and judged | 350 | Historical raw corpus |
| Score at least 7 | 245 | Automatic rejects removed |
| After adversarial spot-check | 242 | Three records dropped |
| Final mixed corpus | 404 | 242 domain / 81 Hermes / 81 Dolly |
| Source train / holdout | 384 / 20 | Stratified 95/5 split |
| T4-safe train / holdout | 328 / 18 | Whole records at no more than 4,096 tokens |

The 18-record bounded holdout tracks validation loss. It is not the 20-task frozen
repository eval under `evals/tasks/frontend-stack/`.

## Final record schema

One JSON object per line:

```json
{
  "messages": [
    {"role": "system", "content": "You are an expert coding assistant operating inside pi."},
    {"role": "user", "content": "Fix the disabled SaveButton in src/SaveButton.tsx."},
    {"role": "assistant", "tool_calls": [{"name": "read", "arguments": {"path": "src/SaveButton.tsx"}}]},
    {"role": "tool", "name": "read", "content": "export function SaveButton() { ... }"},
    {"role": "assistant", "tool_calls": [{"name": "edit", "arguments": {"path": "src/SaveButton.tsx", "edits": [{"oldText": "...", "newText": "..."}]}}]},
    {"role": "tool", "name": "edit", "content": "ok"},
    {"role": "assistant", "content": "Fixed the state reset and verified the focused test."}
  ],
  "tools": [
    {"type": "function", "function": {"name": "read", "description": "Read a file", "parameters": {"type": "object"}}}
  ],
  "source": "frontend-stack"
}
```

Actual `tools` arrays use the complete schemas in `training/pi_tools.json`. Domain
records carry all seven pi tools. Re-shaped Hermes records carry their example tools.
Dolly plain-chat records deliberately omit `tools`.

Tool calls stay in the repository's flat `{name, arguments}` representation. The
pinned Qwen3 template accepts both this form and OpenAI's nested `function` form.
Arguments remain JSON objects, matching llama.cpp's server-side template input.

## Integrity rules

- Never copy an eval task, paraphrase, reference diff, or solution fragment into data.
- Never truncate a message, call, result, or trajectory to meet context limits.
- Every assistant tool call must have its complete contiguous tool-result set.
- The formatter must pass both `messages` and `tools`; `source` is metadata only.
- pi-domain validation rejects unknown tool names and argument keys.
- Public-source licenses and conversion decisions stay recorded in
  `frontend-stack/final/MANIFEST.md`.

## Reproduction checks

Validate the pi-converted domain keep set:

```powershell
python scripts/validate_jsonl.py datasets/frontend-stack/filtered/keep_ge7.pi.jsonl --pi
```

Check deterministic mixed-corpus shape without writing:

```powershell
python scripts/build_train_mix.py --demo
```

Reproduce the bounded split inside an environment containing the pinned tokenizer:

```powershell
python scripts/build_short_train.py --check
```

Authoritative bounded hashes and token statistics live in
`frontend-stack/final/train-short4096.manifest.json`.
