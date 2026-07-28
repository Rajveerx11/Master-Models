# Task 09 - Single tab looks lopsided and long names truncate too early

Source: `C:\terax-ai` commit `9d144ee` (src/modules/tabs/TabBar.tsx)
Difficulty: **medium**
Start state: `git -C "C:\terax-ai" checkout 9d144ee~1`

## Prompt (given to the agent verbatim)

Three tab-bar problems: with only one tab open the padding is uneven because it reserves space for a close button layout it does not need, file names truncate far earlier than the available width, and the keyboard-shortcut hint in the overflow menu uses an inconsistent separator. Fix all three.

## Success criteria (checkable)

- [ ] A lone tab has symmetric horizontal padding; multi-tab layout is unchanged
- [ ] Tab label max width is increased in both compact and normal density
- [ ] Shortcut hints render through the shared formatting helper rather than ad-hoc string joins
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 9d144ee` (graders only - never shown to a model).
