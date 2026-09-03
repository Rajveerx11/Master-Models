# Task 09 - Small model omits empty required arrays

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `a80e1e37f0d261f87c27011220314d9e926258d9`
Start commit: `663557a3565cda97e17cc55e9c9b3f4acf7d760e`
Difficulty: **medium**
Category: schema-boundary integration

## Prompt (given to the agent verbatim)

The CI model often omits required array fields when their natural value is empty and produces concise but non-empty summaries. The Rust tool schemas are stricter than their Zod mirrors, causing valid-enough artifacts to fail before downstream validation. Align the contracts and normalize only missing required arrays without masking missing scalar fields.

## Success criteria (checkable)

- [ ] Rust string constraints match the corresponding Zod acceptance boundary.
- [ ] Missing required array properties are inserted as empty arrays before schema validation.
- [ ] Existing values are never overwritten.
- [ ] Missing required non-array properties still fail validation.
- [ ] Snapshot expectations and live golden assertions reflect the corrected contract.
- [ ] Unit tests cover both normalization and non-array rejection behavior.

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib normalize_missing_arrays
pnpm --filter @testing-ide/shared test
```

## Scoring: pass / partial / fail notes

- **pass** - contracts align and normalization is narrow, recursive behavior is not invented, and tests prove boundaries.
- **partial** - main case works but existing values or missing scalars are mishandled.
- **fail** - validation is broadly weakened or arbitrary missing fields are fabricated.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 663557a3565cda97e17cc55e9c9b3f4acf7d760e -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference lowers mismatched Rust `minLength` values, calls `normalize_missing_arrays` before validation, adds two boundary tests, refreshes snapshots, and adjusts the golden objective assertion. Inspect with `git -C "C:\Testing IDE" show a80e1e37f0d261f87c27011220314d9e926258d9`.
