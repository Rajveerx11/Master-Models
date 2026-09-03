# Task 05 - Clean control refactors window-control presentation

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `182597ffafcd1acaf58b522bc7126d5c835f8b9d`
Start commit: `5d136a2733bedfb841a3a6592c59d4cd086e862f`
Difficulty: **easy**
Task mode: **review**
Patch files: `src/components/WindowControls.tsx`, `src/modules/header/Header.tsx`
Patch base: `5d136a2733bedfb841a3a6592c59d4cd086e862f`
Patch target: `182597ffafcd1acaf58b522bc7126d5c835f8b9d`
Patch direction: **clean-forward**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review returns no actionable correctness finding for the icon and sizing refactor
- [ ] Review recognizes that minimize, maximize/restore, and close handlers and accessible labels remain wired
- [ ] Review does not elevate subjective icon, spacing, hover, or platform-style preferences into defects

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **no findings expected**.

Reference solution: `git -C "C:\terax-ai" show 182597ffafcd1acaf58b522bc7126d5c835f8b9d` (graders only - never shown to a model).

Forward patch replaces inline SVGs with existing icon components, standardizes button styling, and removes a divider. Window commands and labels remain unchanged.
