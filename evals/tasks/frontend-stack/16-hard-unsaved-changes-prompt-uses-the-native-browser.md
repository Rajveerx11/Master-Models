# Task 16 - Unsaved-changes prompt uses the native browser dialog

Source: `C:\terax-ai` commit `a628d62` (src/app/App.tsx)
Difficulty: **hard**
Start state: `git -C "C:\terax-ai" checkout a628d62~1`

## Prompt (given to the agent verbatim)

Closing a dirty editor tab pops the raw native confirm dialog, which looks nothing like the rest of the app. Replace it with the app's own dialog component, keeping the same two choices.

## Success criteria (checkable)

- [ ] Native confirm is gone from the close path
- [ ] The styled dialog offers Cancel and Close Anyway with equivalent behaviour
- [ ] Cancel leaves the tab open and dirty; Close Anyway disposes it
- [ ] The dialog is keyboard dismissible and returns focus sensibly
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show a628d62` (graders only - never shown to a model).
