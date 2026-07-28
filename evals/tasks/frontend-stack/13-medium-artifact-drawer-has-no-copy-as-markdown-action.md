# Task 13 - Artifact drawer has no Copy as Markdown action

Source: `C:\Testing IDE` commit `1f8aed9` (apps/desktop/src/components/ai-panel/artifact-detail-drawer.tsx)
Difficulty: **medium**
Start state: `git -C "C:\Testing IDE" checkout 1f8aed9~1`

## Prompt (given to the agent verbatim)

The artifact detail drawer can save an artifact as a .md file and copy it as TSV, but there is no way to copy the rendered markdown straight to the clipboard. Add that action to the export menu, matching how the existing actions behave.

## Success criteria (checkable)

- [ ] New menu item copies the artifact markdown body to the clipboard
- [ ] It reuses the existing export busy/status/error mechanics rather than new ad-hoc state
- [ ] It is disabled or a no-op when no artifact detail is loaded
- [ ] Existing export actions are unchanged
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\Testing IDE" show 1f8aed9` (graders only - never shown to a model).
