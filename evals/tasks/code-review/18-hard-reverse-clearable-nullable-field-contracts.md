# Task 18 - Reverse patch makes nullable fields impossible to clear

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `8aa400c1c18eeb70c6b1c9e735d3862cdf572a39`
Start commit: `510069be2cab52f86a6b40e9f8cadf855079f171`
Difficulty: **hard**
Task mode: **review**
Patch files: `apps/server/src/models/board.rs`, `apps/server/src/models/issue.rs`, `apps/server/src/models/mod.rs`, `apps/server/src/models/sprint.rs`, `apps/server/src/models/user.rs`, `apps/server/src/routes/boards.rs`, `apps/server/src/routes/sprints.rs`, `apps/server/src/services/auth_service.rs`, `apps/server/src/services/board_service.rs`
Patch base: `8aa400c1c18eeb70c6b1c9e735d3862cdf572a39`
Patch target: `510069be2cab52f86a6b40e9f8cadf855079f171`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that `Option<T>` cannot distinguish omitted update fields from fields explicitly set to JSON null
- [ ] Review explains that clients can set nullable values but cannot later clear them across the affected board, issue, and sprint paths
- [ ] Review also identifies the non-null `password_hash` model contract conflicting with nullable external-auth users

## Verification commands

`cargo test --manifest-path apps/server/Cargo.toml`

## Scoring: pass / partial / fail notes

- **pass** - reports both the clearability contract regression and nullable-password regression with precise evidence.
- **partial** - reports only one regression or gives incomplete trigger/impact analysis.
- **fail** - misses both defects, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **two findings expected**.

Reference solution: `git -C "C:\Testing IDE" show 8aa400c1c18eeb70c6b1c9e735d3862cdf572a39` (graders only - never shown to a model).

The reverse patch collapses clearable update fields from `Option<Option<T>>` to `Option<T>`, so JSON null is indistinguishable from omission and stored values cannot be cleared. It also restores a non-null `password_hash` even though Supabase-managed users may have no local password hash.
