# Task 18 - Ctrl+L is swallowed instead of clearing the terminal

Source: `C:\terax-ai` commit `90b8fb4` (src/app/App.tsx)
Difficulty: **hard**
Start state: `git -C "C:\terax-ai" checkout 90b8fb4~1`

## Prompt (given to the agent verbatim)

Ctrl+L is bound to the AI 'ask about selection' action. When the terminal is focused and nothing is selected, the app still intercepts the key, so the terminal never receives it and the screen will not clear. Let the keypress through in that case without breaking the shortcut when there IS a selection, or when focus is anywhere else.

## Success criteria (checkable)

- [ ] Ctrl+L with terminal focused and no selection reaches the terminal and clears it
- [ ] Ctrl+L with an active terminal selection still triggers the AI action
- [ ] Ctrl+L outside the terminal is unchanged
- [ ] The existing editor undo/redo suppression logic still works
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 90b8fb4` (graders only - never shown to a model).
