# Task 08 - Reverse patch replays partial TUI output after hibernation

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `65209b3e87fca0138b0447bfd04266bc97e254b4`
Start commit: `ee1c9bb5188b4c8cda40bb3301e9b9385debce28`
Difficulty: **medium**
Task mode: **review**
Patch files: `src/modules/terminal/lib/rendererPool.ts`, `src/modules/terminal/lib/useTerminalSession.ts`
Patch base: `65209b3e87fca0138b0447bfd04266bc97e254b4`
Patch target: `ee1c9bb5188b4c8cda40bb3301e9b9385debce28`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that alternate-screen sessions replay a capped ring of incremental cursor updates onto a stale snapshot
- [ ] Finding explains why dropped early frames corrupt a resumed TUI and why append-only shells differ
- [ ] Review recommends discarding dormant TUI bytes and forcing a repaint while preserving normal shell replay

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the affected area but gives incomplete, weakly evidenced, or miscalibrated analysis.
- **fail** - misses the proven defect, invents a defect on a clean control, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\terax-ai" show 65209b3e87fca0138b0447bfd04266bc97e254b4` (graders only - never shown to a model).

Reverse patch removes alternate-screen capture, dormant-ring discard, and PTY resize kick. Reference stores state at release, discards TUI bytes, and triggers SIGWINCH on rebind.
