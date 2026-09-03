# Task 07 - Reverse patch evicts terminal renderers without TUI awareness

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `5af83990305d4d18286962c9a3a2086f056b46d7`
Start commit: `f324da58c287c97b44a47966254e558a805208c1`
Difficulty: **medium**
Task mode: **review**
Patch files: `src/modules/terminal/lib/rendererPool.ts`
Patch base: `5af83990305d4d18286962c9a3a2086f056b46d7`
Patch target: `f324da58c287c97b44a47966254e558a805208c1`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that renderer victim selection ignores alternate-screen state and can evict a live TUI before safer shell slots
- [ ] Finding explains screen corruption or lost interactive state when the renderer is recycled
- [ ] Review cites the pool selection logic and recommends retaining TUI/focused preference rather than a style-only complaint

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\terax-ai" show 5af83990305d4d18286962c9a3a2086f056b46d7` (graders only - never shown to a model).

Reverse patch restores a four-slot, oldest-unfocused victim policy with no alternate-screen weighting and removes cursor restoration. Reference scores alternate-screen and focused slots as expensive victims.
