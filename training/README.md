# Training — Unsloth QLoRA

Trainer: **Unsloth** (already installed locally / Unsloth Studio). No Claude needed
for any step here — this all happens after dataset week.

## Recipe per specialist

- Base: `unsloth/Qwen3-8B` (4-bit)
- Method: QLoRA — r=16, alpha=32, dropout=0, target all attention + MLP proj layers
- Data: `datasets/<domain>/final/train.jsonl` — built from
  `datasets/frontend-stack/filtered/keep_ge7.pi.jsonl` (**the pi-schema file, never
  the authoring one**). 242 domain trajectories at 60% of the mix ⇒ **~404 total**:
  242 domain / ~81 general tool-calling / ~81 general instruction (60/20/20).
  The old "~2K, 60/20/25" figure was wrong twice — 2K no longer exists, and 60/20/25
  sums to 105%.
- Chat template: **Qwen3 template with tool-call support — must byte-match what
  llama.cpp serves later.** Template mismatch silently destroys tool calling; this
  is the #1 failure mode to check.
- Epochs: 2-3 (watch eval loss, small sets overfit fast) · lr 2e-4 cosine ·
  batch: whatever fits with gradient accumulation to effective 16
- Hold out 5% of train.jsonl as validation — this is NOT the frozen eval, just
  loss tracking.

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
