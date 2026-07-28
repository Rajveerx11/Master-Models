# Task 20 - AI panel is a rainbow of accent colours

Source: `C:\Testing IDE` commit `5869b86` (Frontend/src/components/features/ai-panel/AiActionPanel.tsx + FileExplorer.tsx)
Difficulty: **hard**
Start state: `git -C "C:\Testing IDE" checkout 5869b86~1`

## Prompt (given to the agent verbatim)

The AI panel gives every action its own colour (blue, emerald, amber, purple, rose, indigo) plus a pulsing dot in the header - it reads as a toy, not a professional tool. Rework it to a monochromatic treatment that relies on hierarchy and spacing instead of hue. Also: the Open Folder button in the file explorer only appears when no folder is loaded; make it always available.

## Success criteria (checkable)

- [ ] Per-action accent colours and background tints are removed; the panel reads monochromatic
- [ ] Hierarchy is preserved through type scale, weight and spacing rather than colour
- [ ] Decorative animated indicator is gone
- [ ] Open Folder is reachable at all times, including when a folder is already open
- [ ] No dead imports or unused style props left behind
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\Testing IDE" show 5869b86` (graders only - never shown to a model).
