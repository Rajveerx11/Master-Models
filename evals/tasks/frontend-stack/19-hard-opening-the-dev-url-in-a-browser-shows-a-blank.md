# Task 19 - Opening the dev URL in a browser shows a blank, broken page

Source: `C:\Testing IDE` commit `581e9cb` (src/components/browser-notice.tsx (new) + src/main.tsx)
Difficulty: **hard**
Start state: `git -C "C:\Testing IDE" checkout 581e9cb~1`

## Prompt (given to the agent verbatim)

The Vite dev server runs on localhost:5173 for hot reload, but this is a desktop app - if someone opens that URL in a normal browser tab every IPC call fails and they get a blank page or a wall of red error toasts. Detect that situation at startup and show a clear explanation of how to launch the real desktop app instead of mounting the broken UI.

## Success criteria (checkable)

- [ ] When no desktop runtime is present, a splash screen renders instead of the app
- [ ] The splash explains why the page cannot work and gives the exact command to start the desktop app
- [ ] Detection covers both desktop runtime versions and does not trip the automated E2E harness
- [ ] Error reporting is not initialised on the splash path
- [ ] Running inside the real desktop shell still mounts the normal app
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\Testing IDE" show 581e9cb` (graders only - never shown to a model).
