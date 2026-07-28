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

**2026-07-28**
- **Judge calibrated**: `prompts/judge-rubric.md` gained worked 3/5/8 anchors,
  anti-anchors, and reasoning-before-score output. Measured effect below.
- **Batch 2 generated + judged**: 25 trajectories across 5 cells (error-states,
  data-fetching, state-mgmt, styling/design-polish, accessibility), 5 parallel
  generators. 25/25 schema-valid, 0 near-dups, pure ASCII / no BOM, tool turns
  avg 6.0, 18/25 carry an error-recovery turn (batch 1: 5/25).
- **Judge mean 6.68** (batch 1: 8.08), median 7, spread 5-8, 0 auto-rejects —
  the anchors moved the scale and widened the distribution.
- Weakest dimension batch-wide: **diversity value**. Archetype-per-generator
  produced five identical bugs per cell, and parallel generators recycled
  recovery gimmicks, domains, and even a ticket id. Batch-3 fixes logged in
  `plan/dataset-generation-research.md`.
- **Frontend evals FROZEN** (commit `f2fb8f1`): 20 tasks mined from real commit
  history in `terax-ai` (17) and Tessera (3), difficulty split 5 easy / 9 medium
  / 6 hard. Each records its start commit, a symptom-only prompt, checkable
  criteria, and a graders-only reference solution. This unblocked scale-up.
- **Batch 3 in flight**: 100 trajectories, 10 generators, contract in
  `prompts/batch3-spec.md` — disjoint cell / archetype / sector / recovery /
  ticket-id slices per generator, plus a 3 easy / 4 medium / 3 hard mix inside
  each one. Generator E landed first (10/10 valid).
- **Throughput lesson**: 10 concurrent generators exhaust the session window
  before any of them writes a file. Waves of 5 are the sustainable shape.
- **Second teacher**: Opus is now the fallback when Fable's window closes.
  Mixed-teacher parts are tagged so judge scores can be compared per teacher.
- **v1 scope revised** in `plan/v1-release-plan.md`: one domain (frontend-stack),
  300-600 raw instead of 2K per domain, and the full remaining path written out
  in four phases to the gate result.
