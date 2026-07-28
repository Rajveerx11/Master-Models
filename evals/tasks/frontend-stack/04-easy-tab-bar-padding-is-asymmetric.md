# Task 04 - Tab bar padding is asymmetric

Source: `C:\terax-ai` commit `30bfd2b` (src/modules/tabs/TabBar.tsx + src/settings/SettingsApp.tsx)
Difficulty: **easy**
Start state: `git -C "C:\terax-ai" checkout 30bfd2b~1`

## Prompt (given to the agent verbatim)

Tabs look off-centre - the padding on the left and right of a tab does not match, and the settings window tab strip is flush against its container edges. Fix the spacing in both places.

## Success criteria (checkable)

- [ ] Editor tab padding is visually balanced in both compact and normal density
- [ ] The settings TabsList has horizontal padding inside its container
- [ ] No height change to either tab strip
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 30bfd2b` (graders only - never shown to a model).
