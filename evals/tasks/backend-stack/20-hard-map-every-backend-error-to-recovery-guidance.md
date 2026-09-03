# Task 20 - Map every backend error to recovery guidance

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `1ee314272aadbfbffb6f76dfa81e9c733e70496e`
Start commit: `9ec127a71b818296b5ac201a2bfd7e926e69a206`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Backend errors expose stable machine codes but no concise recovery guidance for users. Add one safe, actionable recovery message for every application, LLM-provider, and tracker error variant. Wrapped provider and tracker errors must retain their specific advice through the application error boundary. Keep messages free of credentials, payloads, and internal details, and make the mapping exhaustive so future enum changes cannot silently omit guidance.

## Success criteria (checkable)

- [ ] Every application error variant returns a non-empty actionable recovery message
- [ ] Every LLM error variant has provider-appropriate guidance
- [ ] Every tracker error variant has tracker-appropriate guidance
- [ ] Wrapped LLM and tracker errors delegate without losing their specific message
- [ ] Existing stable error codes and display messages remain unchanged
- [ ] Guidance contains no raw secrets, payload previews, or internal diagnostics
- [ ] Exhaustive focused tests and strict Clippy pass

## Verification commands

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib recovery_hint 2>&1; $code = $LASTEXITCODE; $output | Write-Output; if ($code -ne 0 -or $output -notmatch '5 passed') { exit 1 }
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - all three error hierarchies have exhaustive safe guidance and wrapper delegation preserves specificity.
- **partial** - useful guidance exists but a hierarchy, variant, delegation path, or safety constraint is incomplete.
- **fail** - important errors lack guidance, wrapped errors become generic, secrets leak, or checks fail.

## Graders-only reference evidence

The reference adds exhaustive recovery mappings to the application, LLM, and tracker error types, delegates wrapped errors, and adds per-variant plus delegation tests. Inspect with `git diff 9ec127a71b818296b5ac201a2bfd7e926e69a206 1ee314272aadbfbffb6f76dfa81e9c733e70496e -- apps/desktop/src-tauri/src/error.rs apps/desktop/src-tauri/src/providers/llm/error.rs apps/desktop/src-tauri/src/providers/trackers/error.rs`.
