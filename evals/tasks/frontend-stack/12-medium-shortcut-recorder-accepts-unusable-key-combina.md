# Task 12 - Shortcut recorder accepts unusable key combinations

Source: `C:\terax-ai` commit `75e91d0` (src/settings/sections/ShortcutsSection.tsx)
Difficulty: **medium**
Start state: `git -C "C:\terax-ai" checkout 75e91d0~1`

## Prompt (given to the agent verbatim)

In Settings > Shortcuts you can record a binding with no real modifier - or Shift plus a character key, which on many layouts is just a glyph like @ or <. Those bindings type text instead of firing. Reject them at record time.

## Success criteria (checkable)

- [ ] A binding with no Ctrl/Alt/Meta modifier is not recorded
- [ ] Shift plus a single character key is rejected
- [ ] Shift with a non-character key (function/navigation keys) is still allowed
- [ ] Valid modifier combinations record exactly as before
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 75e91d0` (graders only - never shown to a model).
