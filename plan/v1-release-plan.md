# V1 Release Plan — Dataset Sprint + First Specialist

**Date:** 2026-07-24 · **Hard deadline:** Claude (Fable 5) access expires ~2026-07-31.
**Master plan:** `hierarchical-specialist-models.html` (this folder). This file is the
execution plan for v1 only.

## What v1 is

Everything that needs Fable 5, done in 7 days — then one specialist trained and
gated after expiry, using only local tools (Unsloth + llama.cpp).

V1 ships:
1. Frozen eval sets (written first, before any dataset work).
2. Complete filtered datasets for **3 tight domains** (generation needs Claude;
   training doesn't — so we bank datasets now even though only one trains first).
3. One trained specialist (frontend-stack) with a gate result vs stock
   Qwen3-Coder-30B-A3B.

V1 does NOT ship: the 5-model fleet, the fine-tuned orchestrator, any hardware
purchase. Those are conditional on gate wins (see master plan section 08).

## The three v1 domains (tight, not broad)

| # | Domain | Scope (exact, not a discipline) | Trains in v1? |
|---|--------|--------------------------------|---------------|
| 1 | frontend-stack | React + our component/design conventions + CSS | ✅ first |
| 2 | backend-stack | Our API/DB stack: routes, schema, migrations | after gate 1 |
| 3 | code-review | Diff → findings + fixes in our style | after gate 1 |

"Security" and "testing" are deferred — weakest published fit for small models,
and the week is short.

## Day-by-day (the week that matters)

| Day | Work | Needs Claude? | Output |
|-----|------|---------------|--------|
| 1 | Freeze evals: 20 real tasks per domain from repo history. Commit. | No | `evals/tasks/*` frozen |
| 1–2 | Hand-curate 50–100 seed pairs per domain | Helps | `datasets/*/seeds/` |
| 2–4 | Fable generates 5–10K trajectories per domain (`prompts/teacher-generation-prompt.md`) | **YES** | `datasets/*/generated/` |
| 4–5 | Fable judges all trajectories (`prompts/judge-rubric.md`), keep top ~30% | **YES** | `datasets/*/filtered/` |
| 5–6 | Human spot check: 100 random survivors per domain; fix rubric + re-judge if reject rate > 10% | **YES** (re-judge) | QC'd filtered sets |
| 6–7 | Buffer: regenerate weak topics, mix in general/tool-calling data, final JSONL for Unsloth | **YES** | `datasets/*/final/train.jsonl` |

**Rule: anything needing Fable finishes by day 7. No exceptions.**

## After expiry (no Claude needed)

1. Train specialist #1 (frontend-stack) — Unsloth QLoRA on Qwen3 8B (~2K pairs,
   60/20/25 domain/tool-calling/general mix). Configs in `training/`.
2. Export GGUF, serve via llama.cpp.
3. Run the gate: frozen frontend eval, live harness, vs stock Qwen3-Coder-30B-A3B.
4. **Win** → train specialist #2 from banked dataset. **Loss** → STOP training,
   keep harness + datasets as assets, ship stock-30B + escalation setup.

## Budget caps

- Generation: aim $0 extra (covered by existing Claude plan — that's why this week).
- Specialist #1 total: $100 hard cap, 2 weekends of human time.

## Definition of done (v1)

- [ ] Eval sets frozen + committed before first generation prompt ran
- [ ] 3 domains × ~2K filtered, spot-checked trajectory pairs in `datasets/*/final/`
- [ ] Specialist #1 trained, GGUF exported
- [ ] Gate result recorded in `evals/results/` (win or loss — both are done)
