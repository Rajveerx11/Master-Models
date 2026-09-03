# Task 11 - Reverse patch breaks Option-arrow word navigation

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `5f6cb1dce8becaa46730dfb09bea79ed703b1a3c`
Start commit: `ca8baa0fa7d8472c339cf8176c6aa38a5d85b941`
Difficulty: **medium**
Task mode: **review**
Patch files: `src/modules/terminal/lib/keymap.test.mjs`, `src/modules/terminal/lib/keymap.ts`, `src/modules/terminal/lib/rendererPool.ts`
Patch base: `5f6cb1dce8becaa46730dfb09bea79ed703b1a3c`
Patch target: `ca8baa0fa7d8472c339cf8176c6aa38a5d85b941`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that Option+Left and Option+Right stop producing terminal word-navigation sequences
- [ ] Finding explains the macOS terminal interaction and the expected `Escape+b` / `Escape+f` output
- [ ] Review cites the changed key handling and proposes restoring the shared mapping without reporting unrelated renderer-pool edits

## Verification commands

`node --test src/modules/terminal/lib/keymap.test.mjs && pnpm exec tsc --noEmit`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\terax-ai" show 5f6cb1dce8becaa46730dfb09bea79ed703b1a3c` (graders only - never shown to a model).

The reverse patch removes the explicit Option-arrow mapping and its regression cases. Option+Left/Right therefore no longer emit `\x1bb` / `\x1bf`, breaking word-wise cursor movement in terminal applications.
