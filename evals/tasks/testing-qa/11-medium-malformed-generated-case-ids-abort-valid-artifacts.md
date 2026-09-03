# Task 11 - Malformed generated case IDs abort valid artifacts

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `2df8f4cd918a45570d382472bcc3ac4200a35d8c`
Start commit: `4330c35c11db8eeb95d8051e7541d33f468537e6`
Difficulty: **medium**
Category: generated-test normalization

## Prompt (given to the agent verbatim)

Weak local models sometimes emit lowercase identifiers or append a case title to an otherwise recognizable test-case ID. Generation then rejects the entire artifact at schema validation. Add narrow schema-driven normalization for recoverable pattern-constrained IDs, retain authoritative validation for invalid values, and retry the live probe only for transient stream interruption.

## Success criteria (checkable)

- [ ] Recoverable pattern-constrained IDs are uppercased and invalid character runs collapse safely.
- [ ] Already-valid IDs remain byte-for-byte unchanged.
- [ ] Values that cannot satisfy the declared schema pattern remain unchanged for normal validation to reject.
- [ ] Pattern checks use the same JSON-Schema semantics as final validation and cache compiled validators.
- [ ] Stream retries are bounded and apply only to stream-interruption errors.
- [ ] Unit tests cover recoverable, valid, and unsalvageable IDs.

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib normalize_coerces_lowercase_and_titled_case_ids
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib normalize_leaves_valid_and_unsalvageable_ids_untouched
```

## Scoring: pass / partial / fail notes

- **pass** - normalization is schema-driven, cached, narrow, and backed by boundary tests plus selective retry.
- **partial** - common IDs recover but valid/invalid boundaries, caching, or retry filtering is incomplete.
- **fail** - arbitrary IDs are fabricated, final validation is bypassed, or all errors are retried.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 4330c35c11db8eeb95d8051e7541d33f468537e6 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference adds recursive pattern-ID coercion and cached JSON-Schema validators with boundary tests in `generation_service.rs`, plus a two-attempt retry restricted to `StreamInterrupted` in the golden probe. Inspect with `git -C "C:\Testing IDE" show 2df8f4cd918a45570d382472bcc3ac4200a35d8c`.
