# Task 20 - Reverse patch makes sprint completion partial and issue creation invalid

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `e735a593f4d152ae4de634784861056c631bd903`
Start commit: `91a0b70fd6ac02dd476f610e179716dbe35644de`
Difficulty: **hard**
Task mode: **review**
Patch files: `apps/desktop/src/lib/ipc/boards.ts`, `apps/server/migrations/0002_boards_rls.sql`
Patch base: `e735a593f4d152ae4de634784861056c631bd903`
Patch target: `91a0b70fd6ac02dd476f610e179716dbe35644de`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that sprint completion is split into independent network/database operations and can leave partially moved issues or an incorrectly closed sprint
- [ ] Review identifies that issue creation omits the non-null `issue_key` while the database no longer allocates it
- [ ] Findings cite the client/migration contract and propose an atomic completion RPC plus database-side issue-key allocation

## Verification commands

`cargo test --manifest-path apps/server/Cargo.toml && pnpm --filter @testing-ide/desktop typecheck`

## Scoring: pass / partial / fail notes

- **pass** - reports both independently proven regressions with precise evidence and no false positives.
- **partial** - reports only one regression or gives incomplete trigger/impact analysis.
- **fail** - misses both defects, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **two findings expected**.

Reference solution: `git -C "C:\Testing IDE" show e735a593f4d152ae4de634784861056c631bd903` (graders only - never shown to a model).

The reverse patch restores sprint completion as multiple uncoordinated requests, allowing partial state if an intermediate operation fails. It also removes database-side issue-key allocation while the client insert still omits the non-null key, so issue creation can fail.
