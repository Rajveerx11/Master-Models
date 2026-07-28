# Task 02 - Tab icons render at inconsistent stroke weight

Source: `C:\terax-ai` commit `d8e49bc` (src/modules/tabs/TabBar.tsx)
Difficulty: **easy**
Start state: `git -C "C:\terax-ai" checkout d8e49bc~1`

## Prompt (given to the agent verbatim)

The icons in the tab bar do not match each other visually - some strokes are thinner than others. Make the tab icon weights consistent. While you are in there, TabIcon takes a prop it no longer uses; clean that up.

## Success criteria (checkable)

- [ ] All tab icons render at the same stroke width
- [ ] The unused prop is removed from TabIcon and from every call site
- [ ] No unused imports left behind
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show d8e49bc` (graders only - never shown to a model).
