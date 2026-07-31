# V1 Release Plan — Dataset Sprint + First Specialist

**Date:** 2026-07-24 · **Last revised:** 2026-07-28 · **Hard deadline:** Claude access
expires ~2026-07-31.
**Master plan:** `hierarchical-specialist-models.html` (this folder). This file is the
execution plan for v1 only.

## Status at 2026-07-28 (day 5 of 7)

| Item | Planned | Actual |
|------|---------|--------|
| Evals frozen | day 1, 3 domains | frontend-stack only, frozen day 5 (commit `f2fb8f1`) |
| Seed pairs | 50-100 per domain | skipped — batches generate straight from the spec |
| Raw trajectories | 5-10K per domain | 50 judged + 100 in flight (frontend only) |
| Judged | all | batch 1 (mean 8.08, uncalibrated), batch 2 (mean 6.68, calibrated) |
| Domains started | 3 | 1 |

**Two things forced the revision.** Session limits cap throughput at roughly 50-100
trajectories per limit window, not thousands per day. And 10 parallel generators
produce nothing — they exhaust the window before writing a file.

### Revised v1 scope (what actually ships)

- **One domain: frontend-stack.** backend-stack and code-review datasets are dropped
  from v1. Their evals were never written, so generating for them now would violate
  the freeze-first rule anyway.
- **Volume target: 300-600 raw, floor 200.** Not 2K. LIMA-scale curation is the bet:
  ~150-200 kept pairs after the 30% filter, mixed up to ~300-350 total with
  anti-forgetting data.
- **Two teachers.** Fable 5 wrote batches 1-2 and part of batch 3; Opus is the
  fallback teacher when Fable's window closes. Mixed-teacher data is tagged so judge
  scores can be compared per teacher.

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

## Remaining path, end to end

Every step below is either **CLAUDE** (must finish before ~07-31) or **LOCAL** (can
happen any time after). Nothing else is required to reach a gate result.

### Phase 1 — finish the dataset (CLAUDE, by 07-31)

1. **Generate in waves until the window closes.** `prompts/batch3-spec.md` is the
   current contract: 10 generators, disjoint cell / archetype / sector / recovery /
   ticket-id slices, 3 easy + 4 medium + 3 hard per generator. Later batches reuse it
   with a fresh sector list and the next archetype rotation.
   - Launch at most 5 generators per wave. 10-wide reliably yields zero.
   - Any generator that dies on a limit is relaunched verbatim; partial files are
     never patched by hand.
2. **Validate every part on arrival** — `python scripts/validate_jsonl.py <file>`.
   0 FAIL is the gate into judging. Merge parts with a Python script (utf-8, no BOM),
   never PowerShell `Out-File`.
3. **Judge each batch as it lands, not all at the end.** Separate context, rubric +
   calibration anchors from `prompts/judge-rubric.md`. Judging is Claude-dependent, so
   an unjudged batch on 08-01 is a wasted batch.
4. **Spot-check 100 survivors by hand** (or all of them, at this scale). If more than
   10% are bad, fix the weak rubric dimension and re-judge the whole pool — this also
   needs Claude, so it must happen inside the window, not after.

### Phase 2 — assemble the training file (LOCAL)

5. **Select survivors.** Take the top ~30% by judge score across all batches, drop
   every automatic reject regardless of score. Keep the per-cell counts so weak cells
   are visible.
6. **Dedup across batches.** The validator's near-duplicate check runs per file;
   re-run it across the merged pool before training.
7. **Mix in anti-forgetting data** at roughly 60% domain / 20% general tool-calling /
   20% general instruction. Candidate open sources (verify licence and format before
   use): NousResearch Hermes function-calling data, glaive function-calling v2,
   OpenHermes-2.5, Tulu 3 SFT mixture. Convert everything to the same
   `messages` + `tool_calls` shape the domain data uses.
8. **Write `datasets/frontend-stack/final/train.jsonl`**, shuffled, plus a 5% holdout
   for loss tracking only. This holdout is NOT the frozen eval.

### Phase 3 — train and serve (LOCAL)

9. Train per `training/README.md` — Unsloth QLoRA on Qwen3 8B, train-on-responses-only
   masking so tool results and user turns are context, not targets.
10. **Verify the chat template byte-matches what llama.cpp will serve.** Template drift
    silently destroys tool calling and is the single most likely way this fails.
11. Merge LoRA, export GGUF Q4_K_M, serve with `llama-server --jinja`.
12. Smoke test 10 prompts: valid tool JSON, and sane answers to general questions
    (forgetting check). Broken tool JSON means template mismatch — fix that before
    blaming the data.

### Phase 4 — the gate (LOCAL)

13. Run all 20 frozen tasks in `evals/tasks/frontend-stack/` through the live harness
    with the specialist. Each task starts from its recorded `<hash>~1` commit.
14. Run the same 20 with stock Qwen3-Coder-30B-A3B — same harness, same day, same
    scoring.
15. Score each task pass / partial / fail against its own criteria, plus tool-call
    validity rate and right-tool rate. Record in
    `evals/results/<date>-frontend-stack-vs-baseline.md`.
16. **Decision rule.** Specialist beats stock on task completion without a tool-call
    regression → v1 wins, bank the recipe and consider domain #2. Anything else →
    STOP training. Keep the harness guards, the eval set, and the dataset as assets,
    ship stock-30B with the guards, and write the loss up honestly.

### Known gaps that block Phase 4

**RESOLVED 2026-07-31 — the harness is Neura (`C:\Neura`)**, the user's own layer on top
of pi (`@earendil-works/pi-coding-agent`, installed globally at
`%APPDATA%\npm\node_modules`). Neura adds identity, guardrails, memory, checkpoints and a
proof-gate; the TOOLS are pi's built-ins, so pi's tool schema is the contract.

**The tool schema did NOT match, and it would have failed silently.** Authoritative
source: `pi-coding-agent/dist/core/tools/*.js`, `allToolNames = {read, bash, edit, write,
grep, find, ls}`.

| dataset (authoring) | pi (serving) | issue |
|---|---|---|
| `bash {command}` | `bash {command, timeout?}` | ok |
| `grep {pattern, path}` | `grep {pattern, path?, glob?, ignoreCase?, literal?, context?, limit?}` | ok |
| `read_file {path}` | `read {path, offset?, limit?}` | renamed |
| `write_file {path, content}` | `write {path, content}` | renamed |
| `edit_file {path, old_string, new_string}` | `edit {path, edits:[{oldText,newText}]}` | renamed AND restructured |

`edit` is the dangerous one: pi takes an ARRAY of edits. A model trained on the authoring
schema emits a tool pi does not have, with arguments it cannot parse — every edit call
fails, and it would look like training destroyed tool use.

Converting the data is a script; converting after training is impossible. So:
`scripts/to_pi_format.py` performs the transform (structured fields only, never prose)
and `validate_jsonl.py --pi` checks the result against pi's real schema INCLUDING
argument keys.

**Second finding: argument-key drift the validator never caught.** It only checked that
`arguments` is a dict. Across the keep-set: `edit_file` appears with `old/new` (11x) as
well as `old_string/new_string` (318x); `read_file` with `start_line/end_line` (4x) and
`offset/limit` (1x); `grep` with `after_context` and `context_lines`. pi silently DROPS
an argument it does not accept, so this class of drift becomes a mystery eval failure.
`--pi` mode now rejects unknown keys.

Still open:
- Harness guards (malformed tool-call repair-and-retry, empty-file sentinel) exist only
  in `scripts/probe_baseline.py`. Note `probe_baseline.py` also declares the OLD tool
  names and `edit_file {path, old, new}` — it must be updated to pi's schema before it
  is used for any baseline the gate compares against, or the two runs differ.
- **System-prompt fidelity.** Our trajectories carry a one-line system message; pi builds
  its own system prompt at runtime (`dist/core/system-prompt.js`). Training on a system
  line pi never sends is a train/serve mismatch. Decide before training: either train on
  pi's real rendered system prompt, or accept the mismatch knowingly.
- Neura's own extensions (checkpoint, check-gate, guardrail) run per turn and will affect
  eval timing/behaviour. Run the gate with a fixed, recorded Neura config for both the
  specialist and the stock baseline.

## Budget caps

- Generation: aim $0 extra (covered by existing Claude plan — that's why this week).
- Specialist #1 total: $100 hard cap, 2 weekends of human time.

## Definition of done (v1, revised 2026-07-28)

- [x] Frontend eval set frozen + committed (`f2fb8f1`, 20 tasks, 5/9/6 difficulty split)
- [ ] 200+ filtered, spot-checked frontend trajectories in
      `datasets/frontend-stack/final/train.jsonl`
- [ ] Specialist #1 trained, GGUF exported, tool JSON verified against the serving template
- [ ] Gate result recorded in `evals/results/` (win or loss — both count as done)

Dropped from v1: backend-stack and code-review datasets, the 2K-per-domain volume
target, and hand-curated seed pairs. Reasons are in the status table above.

## Honesty note

Eval-freeze rule 1 says tasks are committed before any generation for that domain
begins. Batches 1 and 2 ran before the freeze, as pilots. That ordering is a real
deviation, recorded here rather than quietly ignored. The mitigation is that the eval
tasks were mined from private repo history after those batches were already written,
so no eval task or its wording could have reached a generation prompt. Every batch
from 3 onward runs under the intended order.
