# Task 03 - Reverse patch leaves source-control diff stale after selection changes

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `b58eb80f3d46ef2146c359c6e773a10b953e5b89`
Start commit: `ba0fa69aab53c8d26ad766e192aea224774c5437`
Difficulty: **easy**
Task mode: **review**
Patch files: `src/app/App.tsx`, `src/modules/source-control/useSourceControl.ts`
Patch base: `b58eb80f3d46ef2146c359c6e773a10b953e5b89`
Patch target: `ba0fa69aab53c8d26ad766e192aea224774c5437`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that refreshing to a new first selection updates selection state without loading that file's diff
- [ ] Finding explains the visible blank or stale diff when the previous selected file disappears
- [ ] Review cites `useSourceControl.ts`, proposes loading the replacement selection, and avoids treating the layout line as a bug

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\terax-ai" show b58eb80f3d46ef2146c359c6e773a10b953e5b89` (graders only - never shown to a model).

Reverse patch removes `shouldOpenDiff` and the awaited `loadDiff` call after automatic reselection. Reference also corrects the containing panel height.
