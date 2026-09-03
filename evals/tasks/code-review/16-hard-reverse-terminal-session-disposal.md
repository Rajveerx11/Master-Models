# Task 16 - Reverse patch leaks closed terminal sessions

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `1aa9886fc7a4d895cbda6ed3cd872ea97c5cca96`
Start commit: `731d34bc255284b97a4811b706cafe954105164e`
Difficulty: **hard**
Task mode: **review**
Patch files: `src/lib/fonts.ts`, `src/modules/settings/store.ts`, `src/modules/tabs/lib/useTabs.ts`, `src/modules/terminal/lib/rendererPool.ts`, `src/modules/terminal/lib/useTerminalSession.ts`
Patch base: `1aa9886fc7a4d895cbda6ed3cd872ea97c5cca96`
Patch target: `731d34bc255284b97a4811b706cafe954105164e`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that closing a terminal tab or pane, or resetting the workspace, no longer calls the terminal-session disposer
- [ ] Finding explains that removing UI state alone leaves the backing PTY/session alive, leaking processes, listeners, and memory across repeated closes
- [ ] Review traces all affected tab lifecycle paths and proposes disposing the removed leaf IDs after state selection

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence across the lifecycle paths, correct impact, and no false positives.
- **partial** - notices cleanup removal but misses affected paths, backing-process impact, or a safe correction.
- **fail** - misses the proven defect, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\terax-ai" show 1aa9886fc7a4d895cbda6ed3cd872ea97c5cca96` (graders only - never shown to a model).

The reverse patch removes `disposeSession` calls from tab close, pane close, and workspace reset flows. The leaves disappear from React state, but their module-level sessions and PTYs remain alive, causing cumulative process and resource leaks.
