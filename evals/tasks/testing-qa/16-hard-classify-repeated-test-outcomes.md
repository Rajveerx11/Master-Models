# Task 16 - Classify repeated test outcomes

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `8d99d8eb99c9dabf9fb8a369fa7a9e18f95b5c30`
Start commit: `e3e96e7807d0db75bbf66b3130be9b34b8dcd2df`
Difficulty: **hard**
Category: flakiness classification engine

## Prompt (given to the agent verbatim)

Add a deterministic aggregation layer for repeated sandbox results. For each named test, classify evidence as stable-pass, stable-fail, or flaky; count each verdict; retain one useful failure sample; and serialize the result through the existing Rust contract. Skipped outcomes must not inflate execution ratios, while tests skipped in every run remain non-flaky. Results must not depend on input ordering.

## Success criteria (checkable)

- [ ] Stable pass, stable fail, and mixed outcomes receive distinct verdicts
- [ ] One outcome flip is sufficient to classify a test as flaky
- [ ] Skipped outcomes are excluded from pass/executed ratios
- [ ] Tests skipped in every run are handled deterministically without division errors
- [ ] Aggregate counts exactly match per-test verdicts
- [ ] Failure samples and optional fields serialize consistently
- [ ] Focused pure unit tests pass without Docker, network, or timers

## Verification commands

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib aggregate_flaky 2>&1; $code = $LASTEXITCODE; $output | Write-Output; if ($code -ne 0 -or $output -notmatch '4 passed') { exit 1 }
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib test_verdict_round_trips_through_serde
```

## Scoring: pass / partial / fail notes

- **pass** - pure aggregation is deterministic, skip-aware, internally consistent, and fully serialized.
- **partial** - common verdicts work but ordering, skips, ratios, samples, or serialization has an edge defect.
- **fail** - flaky evidence is misclassified, counts disagree, or focused tests fail.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet e3e96e7807d0db75bbf66b3130be9b34b8dcd2df -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference slice is `apps/desktop/src-tauri/src/providers/runners/mod.rs`, which adds the verdict/result contracts, pure aggregation, and boundary tests. Inspect with `git diff e3e96e7807d0db75bbf66b3130be9b34b8dcd2df 8d99d8eb99c9dabf9fb8a369fa7a9e18f95b5c30 -- apps/desktop/src-tauri/src/providers/runners/mod.rs`.
