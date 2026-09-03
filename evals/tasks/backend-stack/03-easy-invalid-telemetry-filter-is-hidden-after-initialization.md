# Task 03 - Invalid telemetry filter is hidden after initialization

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `2a62e288929457772a38eafe6b060161ad66b763`
Start commit: `e9970d65abb5c337f7b2323dd5bad08bbc463ac8`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

Telemetry initialization correctly rejects an invalid log filter on the first call, but silently accepts the same invalid value after telemetry has already initialized. Make validation deterministic on every call while keeping installation of the global tracing subscriber idempotent.

## Success criteria (checkable)

- [ ] Every call validates the supplied filter before returning success
- [ ] Invalid filters consistently return the existing typed configuration error
- [ ] Repeated valid initialization remains safe and idempotent
- [ ] No global subscriber is installed more than once
- [ ] Telemetry tests pass in any order

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib telemetry
```

## Scoring: pass / partial / fail notes

- **pass** - validation is order-independent and subscriber initialization remains idempotent.
- **partial** - bad filters surface but repeat initialization or typed errors regress.
- **fail** - later invalid filters still return success or tests fail.

## Graders-only reference evidence

Run this ordering discriminator:

```powershell
$source = Get-Content apps/desktop/src-tauri/src/utils/telemetry.rs -Raw
$validation = $source.IndexOf('let filter = EnvFilter::try_new(filter_directive)')
$earlyReturn = $source.IndexOf('if INIT.get().is_some()')
if ($validation -lt 0 -or $earlyReturn -lt 0 -or $validation -gt $earlyReturn) { exit 1 }
```

The validation offset follows the early return at `e9970d65abb5c337f7b2323dd5bad08bbc463ac8`, so the command fails there; it precedes the early return at `2a62e288929457772a38eafe6b060161ad66b763`, so it passes.

The reference moves filter parsing ahead of the `OnceLock` early return in `utils/telemetry.rs`. Inspect with `git diff e9970d65abb5c337f7b2323dd5bad08bbc463ac8 2a62e288929457772a38eafe6b060161ad66b763 -- apps/desktop/src-tauri/src/utils/telemetry.rs`.
