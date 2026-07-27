# Dataset Generation — Research Notes (2026-07-27)

Sources: LIMA (arXiv 2305.11206), Self-Instruct (2212.10560), AgentInstruct (2407.03502),
HF cookbook LLM-judge, Unsloth datasets guide, Hermes-Function-Calling repo, Qwen3 docs.
Distilled against our pipeline (`prompts/`, `datasets/`). Findings → what we changed.

## 1. Quality beats quantity — plan's ~2K filtered target is right
- LIMA: 1K curated examples aligned a 65B model; format consistency + task diversity
  mattered more than volume.
- Unsloth: 100 rows minimum, 1K+ preferred. Our ~2K filtered / domain is comfortably
  in the sweet spot. Do NOT chase 10K raw if judge yield is low — regenerate weak
  cells instead (already in judge-rubric.md process).

## 2. Diversity must be engineered, not hoped for
- Self-Instruct: seed pool + generate + **dedup against everything already kept**
  (ROUGE-L similarity threshold) or the pool collapses to near-duplicates.
- AgentInstruct: explicit taxonomy of skills/flows == our topic matrix. Validated.
- Action: batch prompts get non-overlapping sub-slices per generator (no two
  generators write the same micro-topic), and validation dedups task text before
  judging. Vary file names, component names, project shape per trajectory.

## 3. LLM judge: our rubric survives research contact, two tweaks
- HF cookbook: judges are bad at continuous 0-10; good at small integer scales and
  **additive atomic criteria** — our 5 × 0-2 dimensions is exactly that. Keep.
- Tweak 1: judge must output a short `evaluation` field BEFORE the score
  (reasoning-first improves correlation ~30% in HF's test).
- Tweak 2: judge runs in separate context from generation (already in rubric — enforce:
  different subagent, zero shared conversation).

## 4. Format: OpenAI-messages JSONL is the right interchange
- Qwen3 (our student) natively uses **Hermes-style tool calls** (`<tool_call>` JSON
  in ChatML). Our `messages` + `tool_calls` JSONL converts losslessly via
  `tokenizer.apply_chat_template()` at training time (Unsloth supports Qwen template).
- Training must mask everything except assistant turns (train-on-responses-only) —
  tool results and user turns are context, not targets. Note for `training/`.
- Serving harness (pi/Hermes) is Hermes-format too → tool names in data must match
  harness schema BEFORE scaling generation (datasets/README already warns this).

## 5. Error recovery is high-value signal
- Recovery-from-tool-error turns teach the agent loop more than happy paths.
  Plan's "1 in 5 trajectories include an error to recover from" is supported. Keep
  errors realistic: compiler errors, wrong path, failed grep — not fantasy stack traces.

## 6. Contamination discipline
- Eval tasks: frozen BEFORE generation, never in prompts. **Status: evals/tasks/ is
  still EMPTY** — v1 plan's own DoD says freeze before generation. Batch 1 ran as a
  pipeline pilot (nothing to contaminate yet, evals come from real repo history which
  is not in any prompt), but freezing evals is now the top blocker before scale-up.

## Batch-1 pilot decisions (this run)
- Cell: `forms × bug fix × medium (3-5 tool turns)` — 25 trajectories, 5 generators
  × 5 non-overlapping sub-slices.
- Conventions block: placeholder React 18 + TS + Tailwind guide (seed-derived).
  **Replace with real project conventions before scaling** — biggest quality lever.
- Raw output → `datasets/frontend-stack/generated/raw/` (gitignored by design).

## Design-skill integration (2026-07-27)
Installed to ~/.claude/skills: **taste-skill** (anti-slop rules), **ui-ux-pro-max**
(searchable style/palette/UX database + python scripts), **impeccable** (design
craft reference), **playwright-skill** (browser verify). Skipped huashu-design
(HTML-prototype/slides domain, not React product UI).

Two integration paths for the specialist:
1. **Training-time (primary):** rules distilled into
   `prompts/frontend-design-conventions.md` → pasted as STYLE GUIDE into every
   frontend-stack teacher prompt → specialist internalizes them in weights. Teacher
   (Fable) can additionally consult the full skills during generation. New
   task-type axis added: design-polish.
2. **Inference-time (secondary):** pi/Hermes harness can load a trimmed conventions
   block as a system-prompt module; playwright-skill becomes the EVAL verifier
   (screenshot/interaction checks for frontend gate tasks) — small model never
   needs to read the big skill files.

## Batch-1 results + lessons (2026-07-27, feed into batch 2 prompts)
Result: 25/25 schema-valid (scripts/validate_jsonl.py), 0 near-dup tasks, judge mean
8.08, 0 automatic rejects, scores in `generated/raw/batch1_scores.jsonl`.

1. **Judge too lenient.** Rubric says median 5; separate-context Fable judge gave
   mean 8.08 (self-preference bias, known LLM-judge failure). Before full judging:
   add 2-3 few-shot calibration examples (a 3, a 5, an 8) to the rubric prompt, or
   scores won't separate top 30% meaningfully.
2. **Skeleton monoculture.** All 25 follow locate→read→edit→tsc→summary. Batch 2:
   force skeleton variety per generator (start with grep vs failing test vs read;
   sometimes write_file a new test; sometimes 2-file change).
3. **Verification monoculture.** tsc-only verification for behavioral bugs. Batch 2:
   require ~half the trajectories to run a (fake) vitest/test command as the verify
   step, not just tsc.
4. **Bug-archetype clustering.** Stale-closure/stale-state bugs appeared in ~5/25
   across DIFFERENT sub-slices — sub-slice topics don't prevent archetype collapse.
   Batch 2: assign bug ARCHETYPES per generator too (off-by-one, race, wrong
   operator, missing guard, type mismatch, stale state — one each).
5. **Encoding hygiene.** Generator output had mojibake (â€” for —, âœ“ for ✓) and
   PS5.1 `Out-File utf8` added a BOM. Batch 2 prompts: ASCII-only prose. Merges:
   use python (utf-8, no BOM). Validator now the gate before judging.
