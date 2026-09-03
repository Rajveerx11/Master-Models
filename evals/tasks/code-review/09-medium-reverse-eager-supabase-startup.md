# Task 09 - Reverse patch crashes startup when optional Supabase config is absent

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `255a1bf879c9d4ec59925621b527c864e862567d`
Start commit: `88f22d923d928504d9abe00efa22ca2b53b9a2d1`
Difficulty: **medium**
Task mode: **review**
Patch files: `apps/desktop/src/components/boards/board-panel.tsx`, `apps/desktop/src/components/layout/toolbar.tsx`, `apps/desktop/src/lib/ipc/boards.ts`, `apps/desktop/src/lib/supabase.ts`
Patch base: `255a1bf879c9d4ec59925621b527c864e862567d`
Patch target: `88f22d923d928504d9abe00efa22ca2b53b9a2d1`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies module-load client construction with empty fallback credentials
- [ ] Finding explains that the SDK throws before React mounts even when Boards is unused
- [ ] Review recommends lazy singleton initialization with explicit configuration errors at first feature use and notes all call sites must use it

## Verification commands

`pnpm --filter @testing-ide/desktop build && pnpm --filter @testing-ide/desktop test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\Testing IDE" show 255a1bf879c9d4ec59925621b527c864e862567d` (graders only - never shown to a model).

Reverse patch exports an eagerly constructed client from `supabase.ts` and switches every call site back to it. Without environment variables, bundle evaluation throws before the app shell renders.
