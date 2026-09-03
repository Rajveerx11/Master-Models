# Task 07 - Provider selection is not authoritative

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `eb6bed5e7363b9c542d6ac5bf07c51be3956fd88`
Start commit: `88610471aa4c90f411bd2578dca5a4bc862ca5eb`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Provider selection can leave multiple active rows, while the frontend silently falls back to the first configured provider when no row is active. Make an explicit selection authoritative across persistence and consumers. Activating a connection must be atomic and unique per user; no selection must remain a real state that blocks generation and offers a path to settings without flashing the wrong empty state while data loads.

## Success criteria (checkable)

- [ ] Activating one provider atomically deactivates any currently active provider for the same user
- [ ] Saving an inactive provider does not disturb another active provider
- [ ] Provider selection returns null when no row is explicitly active
- [ ] Generation is blocked with distinct loading, unconfigured, and unselected states
- [ ] Provider switcher text and accessibility labels describe connections consistently
- [ ] Focused repository tests, TypeScript checking, and strict Clippy pass

## Verification commands

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib upsert_active_is_singleton 2>&1; $code = $LASTEXITCODE; $output | Write-Output; if ($code -ne 0 -or $output -notmatch '1 passed') { exit 1 }
pnpm --filter @testing-ide/desktop exec tsc --noEmit
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - persistence guarantees one explicit active connection and every consumer handles no selection honestly.
- **partial** - uniqueness works but fallback, loading, or user guidance remains inconsistent.
- **fail** - multiple active rows or silent provider fallback remains, generation proceeds unselected, or checks fail.

## Graders-only reference evidence

The reference wraps provider activation and upsert in one transaction, adds `upsert_active_is_singleton`, removes the first-row fallback, and separates loading, empty, and unselected UI states. Inspect with `git diff 88610471aa4c90f411bd2578dca5a4bc862ca5eb eb6bed5e7363b9c542d6ac5bf07c51be3956fd88 -- apps/desktop/src-tauri/src/repositories/provider_config_repo.rs apps/desktop/src/lib/provider.ts apps/desktop/src/components/ai-panel/ai-panel.tsx apps/desktop/src/components/layout/status-bar.tsx`.
