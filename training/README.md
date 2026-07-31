# Training — Unsloth QLoRA

Trainer: **Unsloth** (already installed locally / Unsloth Studio). No Claude needed
for any step here — this all happens after dataset week.

## Recipe per specialist

- Base: `unsloth/Qwen3-8B` (4-bit)
- Method: QLoRA — r=16, alpha=32, dropout=0, target all attention + MLP proj layers
- Data: **`datasets/frontend-stack/final/train.jsonl`** — 384 records, built by
  `python scripts/build_train_mix.py` (seed 731, deterministic). Mix is
  242 domain / 81 general tool-calling / 81 general instruction = **404**, split
  384 train + 20 stratified holdout. Sources, licences, and every shape decision are
  in `datasets/frontend-stack/final/MANIFEST.md`. The old "~2K, 60/20/25" figure was
  wrong twice — 2K no longer exists, and 60/20/25 sums to 105%.
- **Each record is `{messages, tools, source}`. The formatter must pass BOTH
  `messages` and `tools` to `apply_chat_template` and ignore `source`.** Dropping
  `tools` removes the `<tools>` block from the prompt and produces exactly the silent
  tool-calling failure this plan keeps warning about — pi always sends tools at serve
  time (`pi-ai/dist/api/openai-completions.js` → `convertTools`).
- `max_seq_length = 8192` — longest record ≈ 6.2k tokens, p90 ≈ 4.5k.
- Chat template: **Qwen3 template with tool-call support — must byte-match what
  llama.cpp serves later.** A copy of Qwen3-8B's template is pinned at
  `training/templates/qwen3-8b.jinja`, and the build renders every record through it,
  so a template break surfaces at build time rather than mid-training. That check uses
  transformers-side Jinja; **the byte-match against `llama-server` itself is still
  required** (minja emits `{"a":1}` where Jinja emits `{"a": 1}`).
- Epochs: 2-3 (watch eval loss, small sets overfit fast) · lr 2e-4 cosine ·
  batch: whatever fits with gradient accumulation to effective 16
- `holdout.jsonl` (20 records) is validation loss only — **not** the frozen eval.
- Train-on-responses-only masking: assistant turns are targets; system, user, and
  tool turns are context.

## Run it

```bash
python scripts/train_qlora.py --check-only   # guards + one formatted sample, no training
python scripts/train_qlora.py                # train
```

Run inside the Unsloth environment. `--check-only` is worth doing first: it runs both
guards and prints a formatted sample so you can see the `<tools>` block with your own
eyes before spending GPU time.

The two guards exist because both failure modes are silent — training completes, loss
looks healthy, and tool calling is dead at serve time:

1. **Template guard** — the tokenizer's `chat_template` must equal
   `training/templates/qwen3-8b.jinja`, the copy the data was built and verified
   against. Unsloth shipping a different Qwen3 template would invalidate that check.
2. **Tools guard** — every record with `tools` must render a `<tools>` block. This is
   the mismatch that was nearly shipped.

## Export + serve

1. Merge LoRA → save merged 16-bit
2. Convert to GGUF Q4_K_M (Unsloth `save_pretrained_gguf` does both steps)
3. Serve: `llama-server -m <model>.gguf --jinja` (--jinja enables the tool-call
   template) — same flags as the existing local-coder setup
4. Point pi/Hermes at it as model name `frontend-stack`

## Gate run (after training) — THREE arms

20 frozen tasks (`evals/tasks/frontend-stack/`) × 3 arms = 60 runs. Same harness,
same day, same recorded Neura config, same scoring.

| Arm | Model | Answers |
|-----|-------|---------|
| A | frontend-stack specialist (trained) | — |
| B | **stock Qwen3-8B (same base, untrained)** | did training do anything? |
| C | stock Qwen3-Coder-30B-A3B | is a small specialist worth a big generalist? |

Arm B is the control and is **not optional**. Without it, A losing to C cannot be
told apart from "8B is a third the size of 30B", and the old two-arm rule killed
the project on that.

Score per arm: task completion (pass/partial/fail), tool-call validity rate,
right-tool rate. Record in `evals/results/<date>-frontend-stack-vs-baseline.md`.
Decision rule lives in `plan/v1-release-plan.md` Phase 4 — all outcomes get committed.

## Sanity checks before the gate (cheap, catch disasters early)

- 10-prompt smoke test: does it still emit valid tool JSON? Does it still answer
  general questions sanely (forgetting check)?
- If tool JSON is broken → chat template mismatch, fix before touching data.
