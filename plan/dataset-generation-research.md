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

## Batch-2 results + lessons (2026-07-28, feed into batch 3)
Cells: 5 x 5 — error-states×bugfix, data-fetching×extend, state-mgmt×refactor,
styling×design-polish, accessibility×review-and-fix. Result: 25/25 schema-valid,
0 near-dups, pure ASCII / no BOM, tool turns avg 6.0 (range 4-8), 18/25 carry an
error-recovery turn (batch 1: 5/25). Judge mean **6.68**, median 7, min 5, max 8,
0 auto-rejects. Scores in `generated/raw/batch2_scores.jsonl`.

What the batch-1 fixes bought:
- **Calibration anchors work.** Mean fell 8.08 -> 6.68 and the distribution
  actually spread (3x5, 7x6, 10x7, 5x8) instead of clustering at 8. Keep them.
- **Skeleton + verification variety worked.** Openers now grep / failing-test /
  bash / read_file; verification now vitest, jest-axe, npm build, tsc.
- **Encoding fixed.** Zero non-ASCII bytes, no BOM, python merge.

New failures to fix in batch 3:
1. **Archetype-per-generator just moved the monoculture inside the cell.**
   Assigning one archetype per GENERATOR produced five identical bugs per cell.
   Fix: one archetype per TRAJECTORY. Cap each archetype at one appearance per
   batch, drawn from a wider pool.
2. **Parallel generators recycle gimmicks and domains.** ENOENT recovery twice,
   edit-fail-then-retry twice, blind test overwrite twice, ticket id "QA-2214"
   in two different files, and EV charging / beekeeping / ski resort / vinyl
   records each invented by two generators. Agents cannot see each other. Fix:
   hand each generator a disjoint, explicit list — domains, recovery gimmick,
   ticket-id range.
3. **Verification incoherence (new automatic-reject candidate).** Several
   trajectories run a "pre-existing" test that asserts copy or behavior invented
   in the same diff. New hard rule for prompts AND rubric: if a test verifies new
   behavior, the trajectory must write that test.
4. **Judge still has no floor.** Nothing scored below 5 and nothing was rejected,
   across two batches. Add a 1-2 anchor and a worked auto-reject example so the
   bottom of the scale is reachable.
5. **Topic matrix is too narrow.** Batch 3 should pull cells not yet touched:
   optimistic updates, i18n, routing, virtualization, file uploads, websockets,
   tables/lists, modals, animations.

## Batch-3 results + the recalibration finding (2026-07-29)

Batch 3: 100 trajectories, 10 generators (spec: `prompts/batch3-spec.md`), one cell
each, 20-archetype rotation, disjoint sectors / recovery modes / ticket ranges, and a
3 easy / 4 medium / 3 hard difficulty mix inside every generator. 100/100 schema-valid,
0 near-dups, pure ASCII, no BOM, tool turns avg 5.7.

### The judge was inflating by ~2.8 points — measured, not guessed

Batch 1 was re-judged on the calibrated scale by a different model (Opus judging
Fable-written data, so no self-preference):

| Batch | Judge | Mean |
|-------|-------|------|
| 1 | uncalibrated | 8.08 |
| 1 | **re-judged, anchored, cross-model** | **5.32** |
| 2 | anchored | 6.68 |
| 3 | anchored | 7.34 |

Same 25 trajectories, same rubric text, 2.76 points apart. The anchors are the only
difference. This also makes the quality trend real and comparable: 5.32 -> 6.68 ->
7.34 across three batches, on one scale.

Combined pool (n=150): mean 6.89, distribution
`{0:1, 4:7, 5:16, 6:17, 7:55, 8:47, 9:7}`.

### What batch 3 got right

- **Difficulty mixing works.** Per-generator 3/4/3 produced a real spread instead of a
  single band, and mirrors the frozen eval's own 5/9/6 split.
- **The fake-test ban bit.** 6 trajectories were caught running a "pre-existing" suite
  that asserts behaviour invented in the same diff. Judges flagged every one.
- **The judge finally rejected something.** Line 4 scored 0: final file calls
  `useState`/`useCallback` with no React import anywhere in the shown content, yet
  `tsc --noEmit` returns clean. First automatic reject in three batches.
- **Two teachers are interchangeable at this task.** Fable-written 7.20 (n=10) vs
  Opus-written 7.36 (n=90). The gap is noise at that n; neither teacher is better.

### What is still wrong — batch 4 fixes

1. **Diversity value is still the weakest dimension** (50 of 100 lines). Capping an
   archetype to once per GENERATOR does not stop the same lesson family recurring
   across the batch: key=index 5x, twMerge class-merge 4x, default-param shadowing 5x.
   Fix: maintain a batch-wide ledger of lesson families and forbid a repeat outright,
   not just per generator.
2. **Recovery motifs recycle within a generator.** "Write to the wrong place, read a
   config, move it" appeared 5x in one half. Assign each of a generator's 3 recovery
   turns a different *shape*, not just a different file.
3. **Ticket-template monoculture.** Judge 1 noted nearly every prompt is the same
   "do X, and warning: bug Y" shape. Batch 4 should vary the ask itself: some tickets
   describe only a symptom with no diagnosis, some are a user quote, some are a
   failing CI log pasted in.
4. **tsc-only verification survives at ~a third of lines** despite the rule. Make it a
   hard per-generator quota checked by the generator before it writes.

## Batch-4 results (2026-07-30) — generation side

Batch 4: 100 trajectories, 10 generators, spec at `prompts/batch4-spec.md`. All four
batch-3 fixes were implemented as *assignment* constraints rather than instructions,
because agents cannot see each other and shared-ledger rules are unenforceable.

| Batch-3 failure | Mechanism used in batch 4 | Held? |
|---|---|---|
| Same lesson recurs batch-wide | 100 named lesson families (20 archetypes x 5 variants); 10 disjoint codes per generator | yes, 10/10 generators used their exact codes |
| Recovery motifs recycle | pool of 15 recovery *shapes*, 3 different per generator, each shape used 2x batch-wide | yes, 10/10 |
| Ticket-template monoculture | old "do X, warning bug Y" shape banned; 8 required ask shapes, task may not name root cause | yes, all 10 covered all 8 |
| tsc-only verification survives | quota raised 6->7 of 10, generator must print its tally before writing | yes, 91/100 test-verified |

Result: 100/100 schema-valid, 0 FAIL, 0 near-dups, 0 non-ASCII, 0 BOM, tool turns
avg 5.8 (range 4-8). Verification: **91 of 100** run a real test, against roughly 67
in batch 3.

### New failure found in batch 4: naming monoculture

Generator A's ten *domains* were distinct but six of its ten invented product names
ended in `-line` (Mainline, Gustline, Meterline, Feederline, Emberline, Copperline).
Disjoint domains do not imply disjoint naming. An explicit anti-formula rule was added
to the remaining generators' prompts mid-batch and worked immediately (H produced
Doorframe / Ironmark Access / Keysafe 4 / PACS Bridge / Rounds / Credentia / Vestibule /
Aperture Nine / Roll Call / Tailgate Watch). Fold the rule into the spec for batch 5.

### Operational lessons

- **Write early, in chunks.** Generator D hit a session limit during its final
  self-check but had already written all 10 lines, so the work survived and validated
  clean. Generators that plan all ten before writing lose everything.
- **Rolling backfill beats fixed waves.** Launching the next letter as each generator
  lands keeps 5 running continuously instead of idling at the end of a wave.
- **Judge in units of 25, not 50.** A session limit then costs 25 scores, not 50.
- Two teachers is now one: Fable 5 hit its limit at the start of this batch
  ("You've reached your Fable 5 limit"). All 100 lines are Opus-written.

## Batch-4 judging (2026-07-30) — four new defects, all systematic

Judged in 4 slices of 25 (not 2 of 50) so a session limit costs 25 scores, not 50.
Result: **mean 6.76, median 7**, distribution `{0:4, 4:2, 5:7, 6:20, 7:30, 8:30, 9:7}`.
67 of 100 at or above the keep bar. Weakest dimension: code_quality 37,
trajectory_logic 31, diversity_value 26, task_realism 6.

Trend on one calibrated scale: 5.32 -> 6.68 -> 7.34 -> 6.76. Batch 4 is DOWN on batch 3,
and the drop is real, not noise — see generator D below.

### Per-generator spread is the finding

| Gen | Mean | >=7 | Rejects |
|---|---|---|---|
| J | 8.0 | 10/10 | 0 |
| G | 7.7 | 9/10 | 0 |
| I | 7.4 | 8/10 | 0 |
| H | 7.3 | 9/10 | 0 |
| F | 7.1 | 8/10 | 0 |
| B | 7.0 | 6/10 | 0 |
| E | 6.7 | 6/10 | 0 |
| A | 6.2 | 5/10 | 0 |
| C | 6.1 | 3/10 | 0 |
| **D** | **4.1** | 3/10 | **4** |

D carries every automatic reject in the batch and drags the mean down about 0.27 on its
own. Two causes, both actionable:
1. **D is the generator that hit a session limit before running its own self-check.**
   Its file was schema-valid but never semantically reviewed. The self-check is
   load-bearing, not ceremony.
2. **D drew ten conceptually adjacent lessons.** The batch-4 archetype numbering was
   ordered by category, so D's contiguous range 7-16 was almost all lifecycle/cleanup.
   Fix in batch 5: interleave the archetype numbering by category so any contiguous run
   of 10 spans data, effect, async, identity and CSS bugs.

### The four new defects (batch-5 FIX 5-8)

1. **New identifier with no import — the corpus's biggest defect.** All 4 batch-4
   rejects and the 1 batch-3 reject are one shape: an edit introduces `<ToastStack />`,
   `notifyToast`, `useRestockToasts`, `<AlertRuleRow />` or `useState` and no import is
   ever added, so the file cannot compile — next to a fabricated green test.
2. **Fabricated green test output.** Raising the verification quota to 7/10 worked on
   volume (91/100 run a real test vs ~67 in batch 3) but generators cannot execute
   anything, so pressure to show a test run produces invented pass output: `getByText`
   that would collide on two nodes, assertions opposite to the implemented comparator,
   ambiguous `getByRole` regexes. **tsc-only was honest and shallow; a fake green test
   is worse, because it teaches that claiming success counts as verifying it.**
3. **Summary claims with no tool result behind them.** The most common complaint across
   all four judges: summaries asserting hook internals, parent spacing or what a
   consumer renders when that file was never opened. One line claims "the rendered DOM
   was identical before and after" from a check it never ran.
4. **Teleporting to the file path.** 5 lines opened an exact deep path with no discovery
   step when the ticket named none. Skeleton variety governs which tool opens a
   trajectory; it does not force the agent to actually look.

### Methodology caveat — judge variance is now unmeasured

Slice means ran 6.64 / 5.40 / 7.4 / 7.6 across four different judges. That spread
confounds generator quality with judge strictness, and batch 4 used twice as many judges
as batch 3. One judge also self-calibrated by pulling batch 3's distribution and scoring
against it, which anchors to the previous batch rather than to the rubric. Cheap fix:
give every judge the same 5 shared control lines and measure the spread directly before
trusting any cross-slice comparison.

### Keep-set at 250 raw

`filtered/keep_ge7.jsonl` rebuilt across all four batches: **176 of 250 (70.4%)**, 5
automatic rejects excluded. Per batch: b1 5/25, b2 15/25, b3 89/100, b4 67/100.

Note the tension: judge-rubric.md still says "keep top ~30%", written when the plan
assumed 5-10K raw. At 250 raw, 30% is 75 trajectories — far under the 200 floor. The
>=7 bar keeping 70% is consistent with the REVISED scope (300-600 raw, 150-200 kept),
not with the original line. The rubric text should be updated to say so rather than
leaving two contradictory targets in the repo.

## Batch-5 results (2026-07-31) — generation side

Batch 5: 100 trajectories, 10 generators, spec at `prompts/batch5-spec.md`. Carries the
four batch-4 mechanisms forward and adds FIX 5-8 from batch-4 judging. Result: 100/100
schema-valid, 0 FAIL, 0 near-dups, 0 non-ASCII, no BOM, tool turns avg 5.8.

All ten generators hit their exact 10 lesson codes, their 3 assigned recovery shapes and
all 8 ticket shapes. Verification: **85 of 100** test-verified (batch 4: 91) — the dip is
one generator (G) sitting exactly at the 7/10 floor.

### The self-check became real work

Batch 4's lesson was that the generator which skipped its own self-check produced every
reject. Batch 5 made the FIX 5-8 re-read explicit, and generators used it to catch their
own defects before writing: re-derived test arithmetic, corrected grep line numbers,
softened a summary from proof to "smoke check", rewrote a duplicated task opener, fixed a
`(value) => void` vs `() => void` assignability bug, removed a dead import. Several ran
FIX 5 programmatically over their own `write_file` bodies rather than by eye.

### Self-reports are reliable on structure, not on prose detail

Checked the self-reported verification tallies against the files mechanically: **10 of 10
generators matched exactly** (85 claimed, 85 measured). Structural claims can be trusted.

Product names in the same reports could NOT be matched at first pass — but that was a
measurement bug (case-sensitive regex against lowercase names in the data), not agent
error. Worth recording because it nearly became a false finding: **verify a claim about
file contents against the file, and check the measurement itself before believing a
surprising result.**

### Name collisions across generators — real, modest, and badly measured

Names appearing in 2+ generator files: batch 3 = 0, batch 4 = 3 (cascade, sentinel,
kestrel), batch 5 = 4 (marguerite in 3 generators, hollis in 3, kestrel 2, sentinel 2).
Agents cannot see each other and disjoint sectors do not constrain naming.

**Caveat: the candidate list was hand-built from names noticed in batches 4-5, so the
batch-3 zero is selection bias.** The 0 -> 3 -> 4 trend is not trustworthy. Proper
measurement needs systematic product-name extraction, not a hand-picked list. A banned
names paragraph was added to `batch5-spec.md` mid-batch; three generators saw it. Its
effect is unmeasured and it addresses a small problem — do not treat it as proven.

### Operational: three distinct failure modes, one rule saved all of them

Fable 5 limit, session limit, and mid-stream stall / watchdog all hit this batch. The
write-early-in-chunks rule preserved partial work every time, and resuming a stopped
agent via its transcript (rather than relaunching) cost as little as 4 tool calls and
kept its knowledge of which lesson codes it had already used. One generator's own notes
said "4 lines written" when the file held 7 — resume instructions must tell the agent to
trust the file over its notes.

### Open spec conflict (batch 6)

Generator J flagged that "spread the 3 recoveries across difficulties" conflicts with the
3-4 turn budget for easy trajectories: a recovery plus a real verification does not fit.
Its recoveries landed hard/hard/medium. Either widen easy to 5 turns when it carries a
recovery, or drop the spread requirement.

## Batch-5 judging — the constraint-load tradeoff

Mean **6.88**, median 7, `{0:1, 4:1, 5:7, 6:22, 7:39, 8:26, 9:4}`, 69/100 above the bar,
**1 reject** (batch 4 had 4). Judged in 4 slices of 25 with the rubric byte-identical to
batches 1-4; the new FIX 6 defect was asked for as a REPORT, not a scoring criterion, so
the trend line stays valid.

### Per-dimension, three batches on one scale

| dimension | b3 | b4 | b5 |
|---|---|---|---|
| tool_correctness | 2.00 | 2.00 | 1.99 |
| trajectory_logic | 1.46 | 1.47 | **1.79** |
| code_quality | 1.51 | 1.05 | **0.94** |
| task_realism | 1.84 | 1.56 | **1.33** |
| diversity_value | 0.57 | 0.89 | 0.88 |
| MEAN | 7.34 | 6.76 | 6.88 |

**This is the most important table in this document.** FIX 5-8 did exactly what they were
written to do: trajectory_logic jumped 1.47 -> 1.79 and rejects fell 4 -> 1. But
`code_quality` and `task_realism` have declined in a straight line for three batches, and
together they cost more than trajectory_logic gained.

**Diagnosis: constraint load is trading against code quality and task realism.** Every
batch has added rules — lesson codes, recovery shapes, 8 ticket shapes, a verification
quota, then FIX 5-8. Generators now spend their budget satisfying constraints rather than
writing substantial, convention-bearing code. Judges say so directly: "a large share of
this range is one-to-five-line fixes with no conventions surface", and several tiny diffs
were docked on scope.

**So batch 6's fix is NOT another constraint.** It is to demand substantial diffs with
real conventions surface, and to drop or merge the rules that are now cheap to satisfy.
Adding a ninth FIX would very likely lower the mean again.

Correction worth recording: mid-analysis I claimed from two judge windows that diversity
had gone backwards. The aggregate says it is flat (0.89 -> 0.88). Window-level dimension
means are noisy across four different judges — do not draw dimension conclusions without
pooling all 100.

### Remaining defects

- **New reject class (line 48).** A refactor changed a hook's return shape from
  `openings` to `{state, retry}`; the trajectory's OWN grep showed the consumer at
  `ClinicDayPicker.tsx:18` destructuring the old shape, and that file was never opened,
  never updated, and tsc never run. FIX 5 covers new identifiers, not changed export
  shapes. Batch 6 needs: if a refactor changes an exported signature, every consumer the
  trajectory has seen must be updated or explicitly checked.
- **Fabricated green tests: 4 of 100** (was batch 4's dominant soft defect). Two of the
  four are typecheck/`tsc` clean runs rather than test runs, so the honesty rule needs to
  cover tsc output too, not just vitest.
- **Fabricated RED tests: 2** — the over-correction. FIX 6 said "if it would fail, show it
  failing", and generators manufactured plausible reds that the code could not produce
  either. State it symmetrically in batch 6: every run, pass OR fail, must be derivable
  from the shown code.
- **Cross-generator concept clustering.** Lesson families are unique batch-wide, but
  concepts still repeat across generators (4 boolean/operator bugs in one 25-line window;
  missing-effect-cleanup 3x; in-flight-ref double-submit 3x). Uniqueness of the lesson
  does not buy diversity of the concept. Needs a per-concept-family quota across all 100.

### Keep-set at 350 raw

`filtered/keep_ge7.jsonl`: **245 of 350 (70.0%)**, 6 automatic rejects excluded.
Per batch: b1 5/25, b2 15/25, b3 89/100, b4 67/100, b5 69/100. **This clears the plan's
200 floor**, so Phase 1 volume is done and Phase 2 can proceed locally.

## Spot-check of the keep-set (2026-07-31)

Two independent adversarial reviewers read a seeded random sample of 24 kept
trajectories (`random.seed(731)`), NOT scoring them, asking only: would training on
this teach the student something wrong?

**Result: 3 drops of 24 (12.5%)**, which trips the plan's 10% re-judge threshold.
n=24 makes that point estimate weak (interval roughly 3-30%), but both reviewers
independently named the SAME weakness, which is the stronger evidence:

> "verification that does not verify the reported symptom" (A)
> "verification claims that outrun the evidence... ten of the twelve write the test
> after the fix and never observe it red, then assert it fails on the old code" (B)

All three dropped trajectories scored **exactly 7** — right at the keep bar. The
defects cluster at the threshold rather than throughout, which suggests the bar is
about right and the marginal keeps carry the risk.

Dropped (recorded in `filtered/spotcheck_drops.json`): a summary stating a false
React mechanism (repeated setState with the same value is a bailout, so piled
listeners cannot cause the reported flicker); a claim that the compiler will catch
new nullable fields when `JSON.parse` yields `any`; and a summary inventing
corroborating evidence ("looked fine in a still screenshot and wrong while
dragging") nobody reported.

### Machine-checking the finding at n=245

The reviewers' finding is only partly machine-detectable. Measured over the whole
keep-set: **59 of 245 (24%) ever show a failing tool run**, and only **5 (2%)**
make an explicit "fails on the old code" claim with no red run behind it.

That 2% is a FLOOR on a narrow, explicitly-worded sub-case — not a refutation of the
reviewers. "Describes a file it never opened" and "asserts a causal mechanism it
never checked" are semantic and no regex finds them. Do not cite the 2% as evidence
the problem is small.

### Decision: dropped the 3, did NOT re-judge

The plan says >10% triggers a rubric fix plus a re-judge of the whole pool. Overruled
deliberately, for three reasons:

1. **Re-judging does not fix anything.** The defect is generation-time, in batches 1-4,
   which predate FIX 6/7. Re-scoring changes ranking, not trajectories.
2. **It would cost the trend line.** A tightened rubric is a different scale; the
   5.32 -> 6.68 -> 7.34 -> 6.76 -> 6.88 sequence only means something because the
   rubric text never moved.
3. The teacher window was better spent confirming the harness schema, which was a
   silent-failure blocker.

Keep-set is now **242**. The residual risk is explicit: the sample implies roughly
10% of kept trajectories carry an unsupported-verification weakness, concentrated in
batches 1-4. **If the gate shows the specialist confidently asserting unverified
results, this is the first suspect — not the tool schema, not the template.**

### Batch-6 spec items from the spot-check

- **Red baseline or no claim.** A trajectory may only say a test "fails on the old
  code" if it SHOWS the red run. Otherwise it must say the test was written after.
- **The disclaimer is a limit, not a ritual.** Two drops appended an honest "I did not
  open X" and then described X's behaviour anyway. Appending the disclaimer must
  forbid the claim, not license it.
- **`write_file` result line counts must match the content written** (found: 77 lines
  reported as 82).
- The two cleanest trajectories in the sample were both test-first red-then-green with
  a partial fix that stayed red. That is the shape to reinforce.

### Tooling note

`scripts/validate_jsonl.py` counts recovery turns by keyword-matching tool output for
"error"/"not found"/"no matches". Silent recoveries — a file written to the wrong
directory, caught by the next read — produce no such string, so the reported
`recoveries` figure is a floor, not a count. Do not treat it as a metric.
