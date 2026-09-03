# Task 15 - Reverse patch removes context-limit compaction

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `8852301646d2008ea70d0b99ef8fe4f65f05d9d5`
Start commit: `89c308a4df9ae081220793513c75906096fbbd9f`
Difficulty: **hard**
Task mode: **review**
Patch files: `src/modules/ai/lib/agent.ts`, `src/modules/ai/lib/compact.ts`
Patch base: `8852301646d2008ea70d0b99ef8fe4f65f05d9d5`
Patch target: `89c308a4df9ae081220793513c75906096fbbd9f`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that long conversations with large historical tool results are sent to the provider without any context-limit reduction
- [ ] Finding explains that once history approaches the selected model's context window, otherwise valid agent turns fail with an over-limit request instead of retaining recent conversation state
- [ ] Review cites the removed compaction call and proposes restoring bounded elision of older tool outputs while preserving system messages and the recent tail

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the single graders-only expected finding with precise changed-line evidence, the correct long-session trigger and impact, and no unrelated findings.
- **partial** - notices the removed compaction path but does not connect it to model context failure or preservation requirements.
- **fail** - misses the proven reliability regression, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **one finding expected**.

Reference solution: `git -C "C:\terax-ai" show 8852301646d2008ea70d0b99ef8fe4f65f05d9d5` (graders only - never shown to a model).

The reverse patch deletes `compactModelMessages` and sends the full converted history directly. Large older tool outputs can therefore push long sessions beyond the selected model's context window. The removed implementation only elides old tool-result payloads near the limit, never system messages, and keeps the newest eight messages intact.
