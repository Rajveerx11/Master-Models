# Task 19 - Reverse patch leaks an open transaction after cancellation

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `a12a02e5c3f6beb078ff2f39100747ffbd696fc4`
Start commit: `cce4841275819eaa08f5d051f96bcbca564efea1`
Difficulty: **hard**
Task mode: **review**
Patch files: `apps/desktop/src-tauri/src/commands/mod.rs`, `apps/desktop/src-tauri/src/lib.rs`, `apps/desktop/src-tauri/src/repositories/artifact_repo.rs`, `apps/desktop/src/lib/app-menu.ts`, `apps/desktop/src/lib/ipc/system.ts`
Patch base: `a12a02e5c3f6beb078ff2f39100747ffbd696fc4`
Patch target: `cce4841275819eaa08f5d051f96bcbca564efea1`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies the manually issued `BEGIN IMMEDIATE` transaction that remains active across awaited work
- [ ] Finding explains how cancellation or a dropped future can return the pooled connection with the transaction still open
- [ ] Review describes the resulting lock/next-borrow failure and proposes a cancellation-safe transaction guard or equivalent rollback guarantee

## Verification commands

`cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices manual transaction handling but misses cancellation, pooling, or the concrete lock impact.
- **fail** - misses the proven defect, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\Testing IDE" show a12a02e5c3f6beb078ff2f39100747ffbd696fc4` (graders only - never shown to a model).

The reverse patch restores a manual `BEGIN IMMEDIATE` sequence across awaits. If the future is cancelled before explicit commit or rollback, the pooled connection can be reused with an open transaction, causing locks and `cannot start a transaction within a transaction` failures.
