# Master Models

Local specialist-model factory: fine-tune small open models (Qwen3 8B base) into
dedicated domain specialists, gated against a stock Qwen3-Coder-30B-A3B baseline,
served locally via llama.cpp and driven by agentic harnesses (pi / Hermes).

**This is a quality bet, not a cost play.** Token cost is already ~$0 with the stock
local 30B. A specialist ships only if it beats that baseline on a frozen eval of
real repo tasks. See `plan/` for the full (roasted and reshaped) plan.

## Urgent constraint

Claude (Fable 5) access expires in ~1 week. Fable is the dataset teacher + judge.
Therefore: **all dataset generation happens this week.** Training (Unsloth, local)
and evaluation can happen after expiry — they don't need Claude.

## Repo structure

```
plan/        Master plan (visual HTML + v1 release plan)
evals/       Frozen eval tasks + rules. WRITTEN FIRST, never used in generation.
prompts/     Teacher generation prompts + judge rubric (the factory's source code)
datasets/    seeds/ -> generated/ -> filtered/ per domain (JSONL trajectories)
training/    Unsloth QLoRA configs + GGUF export notes
```

## Workflow (the factory)

1. **Freeze evals** — 20 real tasks from repo history, before any dataset work.
2. **Seed** — 50–100 hand-curated gold trajectory pairs per domain.
3. **Generate** — Fable 5 expands seeds to 5–10K multi-turn tool-call trajectories.
4. **Judge** — Fable 5 scores against rubric; keep top ~30%.
5. **Spot check** — hand-review 100 random survivors.
6. **Train** — Unsloth QLoRA on Qwen3 8B, ~2K pairs, 60/20/25 domain/tool/general mix.
7. **Gate** — beat stock Qwen3-Coder-30B on the frozen eval in the live harness,
   or STOP.

## Hard rules

- Eval tasks are frozen and never appear in any generation prompt.
- One specialist per whole task at inference — no mid-task model interleaving.
- Every specialist has a kill-gate. Losing a gate is a valid, cheap outcome.

## Progress log

**2026-07-27**
- Research distilled into `plan/dataset-generation-research.md` (quality>quantity,
  engineered diversity, judge calibration, Hermes/Qwen3 format fit).
- **Batch 1 generated + judged**: 25 frontend-stack trajectories
  (`forms × bug fix × medium`), 25/25 schema-valid via `scripts/validate_jsonl.py`,
  judge mean 8.08, 0 auto-rejects. Raw data local-only (gitignored by design);
  5 batch-2 lessons logged in the research note.
- **Design skills integrated**: taste-skill / ui-ux-pro-max / impeccable /
  playwright-skill installed (user-level); distilled into
  `prompts/frontend-design-conventions.md` (97 checkable rules) — now the STYLE
  GUIDE block for frontend generation; judge enforces; `design-polish` task type
  added to the topic matrix.
- **Baseline probed**: stock Qwen3-Coder-30B, 16 edge-case probes
  (`scripts/probe_baseline.py`, informal — not the frozen gate). 9/16 → 11/16
  with harness guards (tool mechanics 9/9). Conventions-in-context stayed 0/5:
  React habits need training, not prompting. Full analysis in
  `evals/results/2026-07-27-baseline-probe.md`.
- **Open blocker**: eval sets still empty — must be frozen (20 real repo tasks
  per domain) before batch-2 scale-up. Claude teacher access expires ~07-31.
