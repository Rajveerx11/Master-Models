# Task 07 - Inline create input vanishes when opened from the context menu

Source: `C:\terax-ai` commit `1c9b532` (src/modules/explorer/InlineInput.tsx)
Difficulty: **medium**
Start state: `git -C "C:\terax-ai" checkout 1c9b532~1`

## Prompt (given to the agent verbatim)

Right-click a folder in the file explorer and choose New File. The inline name input appears and then immediately disappears before you can type anything. Opening the same input from the toolbar button works fine. Fix the context-menu path without breaking real dismissals.

## Success criteria (checkable)

- [ ] Input opened from the context menu stays focused and visible until the user acts
- [ ] Clicking away or pressing Escape still dismisses and cancels as before
- [ ] Toolbar-triggered create is unaffected
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 1c9b532` (graders only - never shown to a model).
