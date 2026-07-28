# Task 06 - Escape in terminal find does not return focus

Source: `C:\terax-ai` commit `b9fef27` (src/app/App.tsx)
Difficulty: **medium**
Start state: `git -C "C:\terax-ai" checkout b9fef27~1`

## Prompt (given to the agent verbatim)

Open a terminal tab, open the find bar, then press Escape. The search UI closes but focus does not go back to the terminal - you have to click the pane before you can type. Focus restore works on editor tabs. Fix it for terminals.

## Success criteria (checkable)

- [ ] Escape in the terminal find field returns focus to the active terminal pane
- [ ] Editor tab focus restore still works
- [ ] No new keyboard shortcut is added
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show b9fef27` (graders only - never shown to a model).
