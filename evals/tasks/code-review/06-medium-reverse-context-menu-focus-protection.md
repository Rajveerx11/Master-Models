# Task 06 - Reverse patch lets context-menu focus restoration cancel editing

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `fe7147d0a7e2d2ad37688e725ddc52d85e4189cb`
Start commit: `6fc8b045f58afa80fd424b21896d5033c3fe8aa2`
Difficulty: **medium**
Task mode: **review**
Patch files: `src/modules/explorer/FileExplorer.tsx`, `src/modules/explorer/FileTreeNode.tsx`
Patch base: `fe7147d0a7e2d2ad37688e725ddc52d85e4189cb`
Patch target: `6fc8b045f58afa80fd424b21896d5033c3fe8aa2`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies Radix context-menu close autofocus stealing focus from a newly mounted rename/create input
- [ ] Finding explains that the resulting blur immediately cancels or discards the inline operation
- [ ] Review cites both root and node context menus and recommends preventing close autofocus only while editing is active

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\terax-ai" show fe7147d0a7e2d2ad37688e725ddc52d85e4189cb` (graders only - never shown to a model).

Reverse patch removes `onCloseAutoFocus` guards from both context-menu contents. Reference prevents restoration only when rename or pending-create state is active.
