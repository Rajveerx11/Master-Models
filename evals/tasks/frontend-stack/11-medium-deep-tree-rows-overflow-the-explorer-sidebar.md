# Task 11 - Deep tree rows overflow the explorer sidebar

Source: `C:\terax-ai` commit `4bc55eb` (src/modules/explorer/FileExplorer.tsx + FileTreeNode.tsx + InlineInput.tsx)
Difficulty: **medium**
Start state: `git -C "C:\terax-ai" checkout 4bc55eb~1`

## Prompt (given to the agent verbatim)

With a deeply nested project, explorer rows push past the sidebar and the panel scrolls sideways - the first characters and icons get clipped on the left. The inline rename input has the same problem and pushes past the right edge. Make names truncate inside the sidebar instead.

## Success criteria (checkable)

- [ ] Long/deep names truncate with ellipsis; no horizontal scrolling of the tree
- [ ] Inline rename and create inputs stay inside the sidebar width
- [ ] Vertical scrolling still works
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 4bc55eb` (graders only - never shown to a model).
