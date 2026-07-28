# Task 08 - File tree drifts left after repeated create/cancel

Source: `C:\terax-ai` commit `6b53098` (src/modules/explorer/InlineInput.tsx)
Difficulty: **medium**
Start state: `git -C "C:\terax-ai" checkout 6b53098~1`

## Prompt (given to the agent verbatim)

In the explorer sidebar, press New File then Escape, several times in a row. Each cycle nudges the whole tree a little further left until names are cut off at the sidebar edge. Reloading resets it. Stop the drift.

## Success criteria (checkable)

- [ ] Tree horizontal position is unchanged after 10+ open/cancel cycles
- [ ] The input is still focused immediately on open
- [ ] Blur-driven refocus behaviour is unchanged
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 6b53098` (graders only - never shown to a model).
