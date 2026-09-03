# Task 02 - Reverse patch uses a display label as a shortcut property

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `8f000c93655687757583211e80c1c1d6d0eebd08`
Start commit: `d5d3802a8a140316ccb453ec5c291485ae3fdbd5`
Difficulty: **easy**
Task mode: **review**
Patch files: `src/lib/platform.ts`, `src/modules/shortcuts/shortcuts.ts`
Patch base: `8f000c93655687757583211e80c1c1d6d0eebd08`
Patch target: `d5d3802a8a140316ccb453ec5c291485ae3fdbd5`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that the computed key is a display token rather than the `meta` or `ctrl` property consumed by shortcut matching
- [ ] Finding explains why configured shortcuts lose their modifier and can match bare letter keys
- [ ] Review cites the binding definitions and recommends separating display labels from data-property names

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\terax-ai" show 8f000c93655687757583211e80c1c1d6d0eebd08` (graders only - never shown to a model).

Reverse patch removes `MOD_PROP` and builds bindings with `MOD_KEY` (`⌘` or `Ctrl`) as an object property; `matchBinding` reads `meta`/`ctrl`, so modifiers disappear.
