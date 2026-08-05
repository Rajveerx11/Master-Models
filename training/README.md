# Training — Unsloth QLoRA

Trainer: **Unsloth** (already installed locally / Unsloth Studio). No Claude needed
for any step here — this all happens after dataset week.

## Recipe per specialist

- Base: `unsloth/Qwen3-8B` (4-bit)
- Method: QLoRA — r=16, alpha=32, dropout=0, target all attention + MLP proj layers
- Source mix: `datasets/frontend-stack/final/train.jsonl` — 384 records, built by
  `python scripts/build_train_mix.py` (seed 731, deterministic). Full frozen holdout
  remains `holdout.jsonl` (20 records) and is never training input.
- Training mix: **`datasets/frontend-stack/final/train-short4096.jsonl`** — built by
  `python scripts/build_short_train.py`. It keeps only complete source records whose
  exact pinned-Qwen render plus TRL terminal token is ≤4096 tokens; it never truncates a string, turn, tool
  call, or tool result. Its JSON manifest records source/template hashes, counts, token
  range, and the unchanged holdout hash. Rebuild it whenever source data or pinned
  template changes.
- **Each record is `{messages, tools, source}`. The formatter must pass BOTH
  `messages` and `tools` to `apply_chat_template` and ignore `source`.** Dropping
  `tools` removes the `<tools>` block from the prompt and produces exactly the silent
  tool-calling failure this plan keeps warning about — pi always sends tools at serve
  time (`pi-ai/dist/api/openai-completions.js` → `convertTools`).
- `max_seq_length = 4096` — 328 whole training records, including 174/230 domain
  trajectories (53.0% specialist share). The 4608-token candidate restored 215 domain
  trajectories but its deterministic 4587-token one-step probe OOMed on RTX 4060 8 GB.
  This cap must pass its deterministic longest-record one-step hardware probe before a full run.
- Chat template: **Qwen3 template with tool-call support — must byte-match what
  llama.cpp serves later.** A copy of Qwen3-8B's template is pinned at
  `training/templates/qwen3-8b.jinja`, and the build renders every record through it,
  so a template break surfaces at build time rather than mid-training. That check uses
  transformers-side Jinja; **the byte-match against `llama-server` itself is still
  required** (minja emits `{"a":1}` where Jinja emits `{"a": 1}`).
- Epochs: 2-3 (watch eval loss, small sets overfit fast) · lr 2e-4 cosine ·
  batch: whatever fits with gradient accumulation to effective 16
- `holdout-short4096.jsonl` (18 whole records) is bounded validation loss tracking
  only — **not** the frozen eval. Its source is the 20-record `holdout.jsonl`; the
  two over-cap records are excluded, never moved into training.
- Train-on-responses-only masking: assistant turns are targets; system, user, and
  tool turns are context.

## Run it

```bash
python scripts/build_short_train.py            # deterministic 4096-token bounded split
python scripts/build_short_train.py --check    # prove split/manifest reproduce exactly
python scripts/train_qlora.py --check-only   # guards + one formatted sample, no training
python scripts/train_qlora.py --probe-longest --output-dir outputs/frontend-stack/probe-longest
python scripts/train_qlora.py                # train
python scripts/train_qlora.py --resume-from-checkpoint outputs/frontend-stack/checkpoint-24
python scripts/export_gguf.py                # merge LoRA + export Q4_K_M
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

The script restores the repository-pinned template after model loading because Unsloth
replaces Qwen3's tokenizer template at runtime. On the 8 GB RTX 4060 it also caps each
fused cross-entropy chunk at 0.02 GB; without that budget Unsloth sees negligible free
VRAM after the forward pass and aborts before step 1. Override only after proving a
larger value fits: `--ce-loss-target-gb <GiB>`. On Windows it disables Unsloth's
optional double-buffered gradient offload: that path records cross-stream CUDA events
and can terminate the process after a long backward pass. Single buffering preserves
training semantics and lowers peak VRAM at the cost of some copy/compute overlap.
The optimizer is `paged_adamw_8bit`: ordinary AdamW 8-bit exhausted VRAM on its first
update after 16 accumulated examples, while the paged form can move optimizer pages
through CUDA unified memory when the GPU is full.
It saves after every optimizer step and retains two recent checkpoints, so
`--resume-from-checkpoint` can recover from a late GPU failure.

`--probe-longest` selects the longest rendered training record deterministically,
forces one optimizer step with accumulation 1, and refuses data above `MAX_SEQ`; use it
before the full run. For an arbitrary cheap hardware-path probe:

```bash
python scripts/train_qlora.py --max-steps 1 --gradient-accumulation-steps 1 \
  --output-dir outputs/frontend-stack/probe
```

## Export + serve

1. Run `python scripts/export_gguf.py`; Unsloth merges the LoRA and converts it to
   GGUF Q4_K_M.
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
