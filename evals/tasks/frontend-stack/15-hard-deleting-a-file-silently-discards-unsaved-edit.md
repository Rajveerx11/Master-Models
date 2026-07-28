# Task 15 - Deleting a file silently discards unsaved edits

Source: `C:\terax-ai` commit `6acbfbc` (src/app/App.tsx)
Difficulty: **hard**
Start state: `git -C "C:\terax-ai" checkout 6acbfbc~1`

## Prompt (given to the agent verbatim)

Open a file, type something so the tab shows the dirty dot, then delete that file from the explorer. The tab closes and the buffer is gone with no warning. Deleting a folder can wipe several dirty tabs at once. Closing a dirty tab with the X already prompts - the delete path should behave the same way.

## Success criteria (checkable)

- [ ] Deleting a file with unsaved edits prompts before the tab is disposed
- [ ] Cancel keeps the tab open with its content intact; confirming disposes it
- [ ] Clean (non-dirty) tabs still close immediately with no prompt
- [ ] Folder delete affecting several dirty tabs prompts once and handles them all
- [ ] The existing close-button dialog component is reused, not duplicated
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 6acbfbc` (graders only - never shown to a model).
