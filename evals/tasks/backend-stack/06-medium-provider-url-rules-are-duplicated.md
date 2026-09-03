# Task 06 - Provider URL rules are duplicated

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `aebc2b4746dde65b0febfd36415e1b17869e3b18`
Start commit: `2b30e765180e963b78af85a80cc2343124bf6ea3`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Provider configuration and provider connection testing currently maintain separate copies of the same base-URL normalization rules. Consolidate this backend behavior so both paths use one canonical implementation without changing any provider URL output or IPC contract.

## Success criteria (checkable)

- [ ] One backend helper owns provider-kind URL normalization
- [ ] Both configuration and connection testing use that helper
- [ ] Ollama, LM Studio, OpenAI-compatible, and cloud-provider behavior remains unchanged
- [ ] No new dependency direction or public IPC shape is introduced
- [ ] Desktop backend tests and strict Clippy pass

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - normalization has one owner and all provider behavior is preserved.
- **partial** - duplication is reduced but behavior, coverage, or layering is incomplete.
- **fail** - duplicate rules remain, URL behavior changes, or checks fail.

## Graders-only reference evidence

Run this ownership discriminator:

```powershell
$config = Get-Content apps/desktop/src-tauri/src/services/provider_config_service.rs -Raw
$connection = Get-Content apps/desktop/src-tauri/src/services/provider_connection_service.rs -Raw
$delegations = ([regex]::Matches($connection, 'provider_config_service::normalize_base_url')).Count
if (-not $config.Contains('pub(crate) fn normalize_base_url') -or $delegations -lt 3 -or $connection -match '(?m)^fn normalize_base_url\(') { exit 1 }
```

At `2b30e765180e963b78af85a80cc2343124bf6ea3`, the canonical helper is private and the connection service owns another function; at `aebc2b4746dde65b0febfd36415e1b17869e3b18`, there are three delegations and no duplicate definition.

The reference promotes the existing normalization function in `provider_config_service.rs` to crate visibility and removes the duplicate implementation from `provider_connection_service.rs`. Inspect with `git diff 2b30e765180e963b78af85a80cc2343124bf6ea3 aebc2b4746dde65b0febfd36415e1b17869e3b18 -- apps/desktop/src-tauri/src/services/provider_config_service.rs apps/desktop/src-tauri/src/services/provider_connection_service.rs`.
