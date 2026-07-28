# Task 05 - Inline create row does not line up with tree rows

Source: `C:\terax-ai` commit `edd88ce` (src/modules/explorer/FileExplorer.tsx + FileTreeNode.tsx)
Difficulty: **easy**
Start state: `git -C "C:\terax-ai" checkout edd88ce~1`

## Prompt (given to the agent verbatim)

When you create a new file or folder in the explorer, the inline input row is visibly out of step with the rows around it - the text is a different size, the spacing is tighter, and where every other row has a file icon this one has an empty gap. Make the pending row match the rows it sits between, at root level and inside a nested folder.

## Success criteria (checkable)

- [ ] Pending create row uses the same text size and gap as normal tree rows
- [ ] It shows an icon matching what is being created (file vs folder) instead of blank space
- [ ] Indentation still matches the depth it is being created at
- [ ] Both the root-level and nested-folder create paths are fixed
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show edd88ce` (graders only - never shown to a model).
