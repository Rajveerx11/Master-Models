# Task 14 - Split dividers leak between terminal tabs

Source: `C:\terax-ai` commit `35e1417` (src/modules/terminal/TerminalStack.tsx)
Difficulty: **medium**
Start state: `git -C "C:\terax-ai" checkout 35e1417~1`

## Prompt (given to the agent verbatim)

Split one terminal tab into two panes, then switch to a different terminal tab that has no splits. The divider lines from the first tab are still drawn across the second one. Sessions must keep running in the background, so unmounting the inactive tab is not an option.

## Success criteria (checkable)

- [ ] Divider handles from an inactive tab are not visible on the active tab
- [ ] Inactive tab content is fully non-interactive (no stray hover or drag targets)
- [ ] Background terminal sessions stay alive - switching back preserves scrollback and running processes
- [ ] Inactive tabs are hidden from assistive technology
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 35e1417` (graders only - never shown to a model).
