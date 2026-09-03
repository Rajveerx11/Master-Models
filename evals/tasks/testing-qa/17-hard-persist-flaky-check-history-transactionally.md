# Task 17 - Persist flaky-check history transactionally

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `88de8e225fb4a541a1d04b47a9c73160880da14f`
Start commit: `a901ad0727398012d2946e2b1382f544f51ee382`
Difficulty: **hard**
Category: test-history persistence

## Prompt (given to the agent verbatim)

Persist completed flaky checks and their per-test verdicts behind a focused repository API. Inserts must be atomic, reads must reconstruct typed summaries and details, history must be newest-first with bounded limits, and deletion behavior must preserve historical evidence while safely nulling a removed run reference. Reject empty identifiers and map missing records and corrupt persisted values to stable errors.

## Success criteria (checkable)

- [ ] Additive migration stores check summaries and child verdict rows with explicit foreign-key behavior
- [ ] One transaction inserts a summary and all verdicts without per-row commits
- [ ] Detail reads round-trip verdicts, ratios, samples, and optional run identifiers
- [ ] History lists newest-first and clamps caller limits to a safe range
- [ ] Deleting a run retains its check while clearing the optional run reference
- [ ] Empty IDs, missing checks, and malformed stored values return stable typed errors
- [ ] Repository tests use local temporary SQLite only

## Verification commands

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib flaky_check_repo 2>&1; $code = $LASTEXITCODE; $output | Write-Output; if ($code -ne 0 -or $output -notmatch '[1-9][0-9]* passed') { exit 1 }
```

## Scoring: pass / partial / fail notes

- **pass** - migration and repository provide atomic, bounded, typed, deletion-safe flaky history.
- **partial** - round trips work but transactionality, ordering, limits, deletion, or error mapping is incomplete.
- **fail** - partial history persists, records disappear unexpectedly, corrupt data panics, or tests fail.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet a901ad0727398012d2946e2b1382f544f51ee382 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference slice is migration `0008_flaky_checks.sql` plus `flaky_check_repo.rs` and repository registration. It includes temporary-SQLite tests for validation, round trips, ordering, missing rows, and run deletion. Inspect with `git diff a901ad0727398012d2946e2b1382f544f51ee382 88de8e225fb4a541a1d04b47a9c73160880da14f -- apps/desktop/src-tauri/migrations/0008_flaky_checks.sql apps/desktop/src-tauri/src/repositories/flaky_check_repo.rs apps/desktop/src-tauri/src/repositories/mod.rs`.
