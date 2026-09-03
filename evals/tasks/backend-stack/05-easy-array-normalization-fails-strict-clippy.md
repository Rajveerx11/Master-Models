# Task 05 - Array normalization fails strict Clippy

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `945a2b1dbc2ef32746699750e7d49e3a463aa7d4`
Start commit: `7ad3eecd64c7a7789a75d2ecf22519476956ff45`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

The tool-output array normalizer fails the repository's strict Clippy policy in several option-handling branches. Make the smallest behavior-preserving control-flow cleanup. Preserve every early return, the skip behavior for non-string required entries, and all normalization output.

## Success criteria (checkable)

- [ ] Strict Clippy accepts the option-handling branches
- [ ] Non-object data and malformed schemas still return without mutation
- [ ] Non-string required entries are still skipped
- [ ] Valid missing-array normalization is unchanged
- [ ] Focused tests and strict Clippy pass

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib normalize_missing_arrays
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - the focused control-flow cleanup passes lint with identical behavior.
- **partial** - lint passes through a broader rewrite or one edge behavior changes.
- **fail** - the lint remains, normalization changes, or checks fail.

## Graders-only reference evidence

The reference replaces five manual option matches with behavior-equivalent let-else forms in `generation_service.rs`. Inspect with `git diff 7ad3eecd64c7a7789a75d2ecf22519476956ff45 945a2b1dbc2ef32746699750e7d49e3a463aa7d4 -- apps/desktop/src-tauri/src/services/generation_service.rs`.
