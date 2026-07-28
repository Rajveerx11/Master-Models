# Task 01 - Source-control buttons show the wrong cursor

Source: `C:\terax-ai` commit `108f6a8` (src/modules/source-control/SourceControlPanel.tsx)
Difficulty: **easy**
Start state: `git -C "C:\terax-ai" checkout 108f6a8~1`

## Prompt (given to the agent verbatim)

In the Source Control panel, the Commit and Push buttons still show the default arrow cursor when you hover them, and they show a normal pointer even when they are disabled. Make the hover affordance correct for both states.

## Success criteria (checkable)

- [ ] Both the Commit and the Push button show a pointer cursor when enabled
- [ ] Both show a not-allowed cursor when disabled
- [ ] No other button behaviour or layout changes
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 108f6a8` (graders only - never shown to a model).
