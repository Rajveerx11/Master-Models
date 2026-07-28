# Task 17 - Model dropdowns run off the bottom of the settings window

Source: `C:\terax-ai` commit `9add816` (src/settings/sections/ModelsSection.tsx)
Difficulty: **hard**
Start state: `git -C "C:\terax-ai" checkout 9add816~1`

## Prompt (given to the agent verbatim)

In Settings > Models, the Default model dropdown extends past the bottom of the window when there are many providers, so the lower entries cannot be reached at all. The editor autocomplete model dropdown has the same problem. Make every model option reachable.

## Success criteria (checkable)

- [ ] Both dropdowns are scrollable and every option can be reached
- [ ] The menu fits inside the settings window at its default size
- [ ] Provider group headers still render correctly while scrolling
- [ ] Selection behaviour and keyboard navigation are unchanged
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 9add816` (graders only - never shown to a model).
