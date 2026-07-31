# Judge Rubric (Fable 5 as judge)

Purpose: score every generated trajectory 0–10. Judge runs in a SEPARATE
conversation from generation (no shared context, no self-leniency).

## The keep bar: score >= 7, hard-reject every automatic 0

Revised 2026-07-31. This file previously said "keep top ~30%", written when the
plan assumed 5–10K raw trajectories per domain. That target was abandoned when
session limits capped throughput (see `plan/v1-release-plan.md` status table).

At the real corpus size the old rule inverts the intent: 350 raw x 30% = 105
trajectories, well under the plan's own 200 floor for training. Keeping >= 7
yields 245 of 350 (70%), which matches the revised scope of 300–600 raw and
150–200 kept.

So the bar is an ABSOLUTE quality threshold, not a percentile:

- **Keep score >= 7.** Kept set lives in `datasets/*/filtered/keep_ge7.jsonl`.
- **Drop every automatic 0** regardless of anything else.
- Do NOT re-tune the bar to hit a volume target. If yield is too low, regenerate
  weak cells with a fixed prompt — never lower the bar to pad the count.
- >= 8 would keep ~30% and is the right bar if raw volume ever reaches 1K+.

The judge does not apply this bar. The judge scores; selection happens after.

## Prompt template

```
You are a strict data-quality judge. Score this training trajectory 0-10.
Be harsh: the median trajectory should score 5. Reserve 8+ for flawless.

TRAJECTORY:
{ONE_JSONL_OBJECT}

Score each dimension 0-2, sum = final score:

1. TOOL CORRECTNESS: every tool_call is valid JSON, right tool for the step,
   realistic arguments, no hallucinated tools. (0 = any malformed call)
2. TRAJECTORY LOGIC: steps follow (read before edit, verify after change);
   tool results actually inform the next action; recovery from errors is sane.
3. CODE QUALITY: final code is correct, idiomatic, matches the stated
   conventions, would pass review. (frontend-stack: conventions =
   prompts/frontend-design-conventions.md — check the anti-slop bans hardest.)
4. TASK REALISM: task is something a real developer asks; scope matches a
   5-40 line diff; not toy, not padded.
5. DIVERSITY VALUE: not a near-duplicate of common patterns; teaches something
   the obvious cases don't.

Automatic 0 (reject regardless of other scores) if:
- any tool call is malformed JSON
- the assistant answers without using tools
- file contents in tool results contradict themselves across turns
- the final code would not run/compile

Output the `evaluation` field FIRST (2-3 sentences of reasoning, citing the weakest
dimension by name), then the score. Reasoning-before-score improves correlation.

Output JSON only:
{"evaluation": "<2-3 sentences>", "score": N, "reject_reason": "<or null>", "weakest_dimension": "<name>"}
```

## Calibration anchors (paste into the judge prompt, above the trajectory)

Batch 1 exposed judge leniency: rubric says median 5, judge returned mean 8.08 with
zero rejects. These anchors pin the scale. Score against them, not against vibes.

```
CALIBRATION - these are what 3, 5, and 8 actually look like:

--- SCORE 3 ---
Task: "Fix the validation error on the signup form."
Trajectory: read_file src/Form.tsx (generic 20-line component, no project character)
-> edit_file adding `if (!email) setError('Invalid')` -> bash `npx tsc --noEmit` -> summary.
Why 3: tool calls are well-formed and ordered (TOOL CORRECTNESS 2, TRAJECTORY LOGIC 1
- tsc cannot verify a behavioral fix), but the task is vague boilerplate any tutorial
contains (TASK REALISM 0), the code is generic and ignores the conventions file
(CODE QUALITY 0), and the pattern is the single most common shape in the pool
(DIVERSITY VALUE 0). A clean, competent, worthless example. Most "looks fine"
trajectories belong HERE, not at 8.

--- SCORE 5 ---
Task: "Pasted phone numbers with a trailing space fail validation on the booking form.
Trim before validating."
Trajectory: grep for the validator -> read_file the hook -> edit_file trims input
before the regex test -> bash vitest, passes -> summary naming the fix.
Why 5: specific real bug, correct minimal fix, verification actually exercises the
behavior (TOOL CORRECTNESS 2, TRAJECTORY LOGIC 2, TASK REALISM 1). But the code is
one line with no conventions surface (CODE QUALITY 0) and trim-before-validate is a
well-worn pattern (DIVERSITY VALUE 0). This is the MEDIAN. A correct, verified,
unremarkable fix scores 5, not 8.

--- SCORE 8 ---
Task: "Search results flash the previous query's rows when you type fast."
Trajectory: bash runs the failing test first (real assertion diff) -> read_file the
hook -> edit_file adds AbortController + cleanup -> bash test STILL FAILS, output
reveals the stale-state setter, not the fetch, is the cause -> read_file consumer ->
second edit guards with a request-id ref -> bash green -> summary explaining both
diagnoses.
Why 8: every dimension earns near-full marks - the recovery turn teaches a genuinely
better second diagnosis, the fix is idiomatic and convention-compliant, and the
failing-test-first skeleton is rare in the pool. Reserve 9-10 for this PLUS
flawless conventions adherence and a task you could not have guessed.

Anti-anchors: do NOT award points for verbose summaries, for realistic-looking file
contents alone, or for using many tools. Length is not quality.
```

## Process

0. Every judge request includes the calibration anchors above. Without them the judge
   drifts ~3 points high (measured on batch 1: mean 8.08, zero rejects).
1. Judge every raw trajectory. Batch **25 per request** — a session limit then costs
   25 scores rather than 50, and 4x25 was measurably fine on batches 4-5.
2. Keep score >= 7 (see the keep bar above); hard-reject all automatic-0s.
   Judges must NOT be told the bar — scoring and selection stay separate.
2b. Do not change this rubric mid-corpus. Batches 1-5 are comparable only because
   the text stayed byte-identical. A new defect class gets REPORTED alongside the
   score (as the batch-5 fabricated-green-test check did), not folded into the
   scale. Changing the scale forfeits the trend line.
3. Human spot check: 100 random survivors per domain.
   - If >10% of the spot check is bad → tighten the rubric's weak dimension and
     RE-JUDGE the whole pool. Do not hand-rescue individual examples.
4. Log kept/rejected counts per topic-matrix cell — cells with high reject rates
   get regenerated with a fixed prompt, not padded from other cells.
