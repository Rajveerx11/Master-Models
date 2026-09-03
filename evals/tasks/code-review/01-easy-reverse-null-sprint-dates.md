# Task 01 - Reverse patch maps absent sprint dates to invalid strings

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `b9b5c7b8f95c4cc8087bc7c174318c8a54f67201`
Start commit: `d3babb46caf559689b41de26f8d601864416afce`
Difficulty: **easy**
Task mode: **review**
Patch files: `apps/desktop/src/lib/ipc/boards.ts`
Patch base: `b9b5c7b8f95c4cc8087bc7c174318c8a54f67201`
Patch target: `d3babb46caf559689b41de26f8d601864416afce`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that absent database dates become empty strings instead of the optional value expected by the domain type
- [ ] Finding cites `apps/desktop/src/lib/ipc/boards.ts` and explains invalid ISO parsing or `Invalid Date` behavior
- [ ] Review proposes preserving absence as `undefined` and reports no unrelated findings

## Verification commands

`pnpm --filter @testing-ide/desktop typecheck && pnpm --filter @testing-ide/desktop test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\Testing IDE" show b9b5c7b8f95c4cc8087bc7c174318c8a54f67201` (graders only - never shown to a model).

Reverse patch changes `mapSprint` so null `start_date` and `end_date` become `''`; the reference fix maps them to `undefined`, matching `string | undefined` and datetime validation.
