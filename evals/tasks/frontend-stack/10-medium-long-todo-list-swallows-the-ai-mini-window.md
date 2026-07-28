# Task 10 - Long todo list swallows the AI mini-window

Source: `C:\terax-ai` commit `60df490` (src/modules/ai/components/TodoStrip.tsx)
Difficulty: **medium**
Start state: `git -C "C:\terax-ai" checkout 60df490~1`

## Prompt (given to the agent verbatim)

In the AI mini-window, a long task list keeps growing until it covers the chat and the tool approval buttons, so you cannot approve anything. Cap it and make it scroll, and make the panel read as a distinct section rather than blending into the chat.

## Success criteria (checkable)

- [ ] Task list is height-capped relative to the window and scrolls internally
- [ ] The Todos header stays pinned while only the list scrolls
- [ ] Chat area and approval cards remain visible and clickable with 50+ tasks
- [ ] Cap holds when the window is resized
- [ ] `pnpm exec tsc --noEmit` clean

## Scoring: pass / partial / fail notes

- **pass** - all criteria met, change confined to the named area, no regressions.
- **partial** - core symptom fixed but one or more criteria missed.
- **fail** - symptom persists, code does not compile, or unrelated files rewritten.

Reference solution: `git -C "C:\terax-ai" show 60df490` (graders only - never shown to a model).
