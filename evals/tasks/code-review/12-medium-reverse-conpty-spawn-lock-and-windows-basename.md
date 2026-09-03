# Task 12 - Reverse patch restores ConPTY spawn races and bad Windows basenames

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `7516c0de7d86f33af6e84343c2fbdea3d479390c`
Start commit: `67f6cbbcbaa5e33437c1632af7804b7cb20f909f`
Difficulty: **medium**
Task mode: **review**
Patch files: `src-tauri/src/modules/pty/session.rs`, `src/modules/explorer/FileExplorer.tsx`
Patch base: `7516c0de7d86f33af6e84343c2fbdea3d479390c`
Patch target: `67f6cbbcbaa5e33437c1632af7804b7cb20f909f`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies the removal of process-wide ConPTY spawn serialization and explains the concurrent Windows spawn failure mode
- [ ] Review identifies that splitting only on `/` displays a full Windows path instead of its basename
- [ ] Each finding cites the relevant changed file and proposes the narrow fix without claiming impact on unrelated platforms

## Verification commands

`cargo check --manifest-path src-tauri/Cargo.toml && pnpm exec tsc --noEmit`

## Scoring: pass / partial / fail notes

- **pass** - reports both independently proven regressions with precise evidence and no false positives.
- **partial** - reports only one regression or gives incomplete trigger/impact analysis.
- **fail** - misses both defects, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **two findings expected**.

Reference solution: `git -C "C:\terax-ai" show 7516c0de7d86f33af6e84343c2fbdea3d479390c` (graders only - never shown to a model).

The reverse patch removes the global `SPAWN_LOCK`, permitting the known concurrent ConPTY creation race. It also changes basename extraction back to `/`-only splitting, so a Windows backslash path is rendered as the full path.
