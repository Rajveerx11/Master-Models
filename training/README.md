# Training — Unsloth QLoRA

Trainer: **Unsloth** (already installed locally / Unsloth Studio). No Claude needed
for any step here — this all happens after dataset week.

## Recipe per specialist

- Base: `unsloth/Qwen3-8B` (4-bit)
- Method: QLoRA — r=16, alpha=32, dropout=0, target all attention + MLP proj layers
- Data: `datasets/<domain>/final/train.jsonl` (~2K trajectories, 60/20/25 mix)
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

## Gate run (after training)

1. Run all 20 frozen eval tasks (`evals/tasks/frontend-stack/`) through the live
   harness with the specialist.
2. Same 20 tasks with stock Qwen3-Coder-30B-A3B, same harness, same day.
3. Score: task completion, tool-call validity rate, right-tool rate.
4. Record in `evals/results/<date>-frontend-stack-vs-baseline.md`.
5. Win → next specialist. Loss → STOP (see plan). Both outcomes get committed.

## Sanity checks before the gate (cheap, catch disasters early)

- 10-prompt smoke test: does it still emit valid tool JSON? Does it still answer
  general questions sanely (forgetting check)?
- If tool JSON is broken → chat template mismatch, fix before touching data.
