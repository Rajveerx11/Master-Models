# Task 03 - Settings tab bodies are wired up by hand

Source: `C:\terax-ai` commit `58e842c` (src/settings/SettingsApp.tsx)
Difficulty: **easy**
Start state: `git -C "C:\terax-ai" checkout 58e842c~1`

## Prompt (given to the agent verbatim)

SettingsApp keeps a TABS array for the tab strip, but deciding which section body to render is done separately by hand, so adding a settings tab means editing two places and it is easy to wire one up wrong. Make the tab definition the single source of truth for both the strip and the body.

## Success criteria (checkable)

- [ ] Each tab entry carries its own section component
- [ ] The rendered body is looked up from the active tab entry, not from a separate branch
- [ ] Adding a new tab requires touching only the TABS array
- [ ] All four existing tabs still render their correct section
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 58e842c` (graders only - never shown to a model).
