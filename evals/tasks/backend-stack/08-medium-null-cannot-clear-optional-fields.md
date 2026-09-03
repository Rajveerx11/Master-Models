# Task 08 - Null cannot clear optional fields

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `4c1974b70eb8025882c1ebf5a9c5a97a10e8e839`
Start commit: `f33a9b1b0ba544c8312d230367c0f521f5e11593`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

PATCH requests currently treat an omitted optional field and an explicit JSON `null` as the same value, so clients cannot clear board descriptions, sprint dates/goals, or column WIP limits. Preserve the three states—omit, clear, and set—through deserialization and service updates. Also align password login with the nullable database column used by externally authenticated users.

## Success criteria (checkable)

- [ ] Omitted nullable update fields preserve their stored values
- [ ] Explicit `null` clears board description, sprint goal/dates, and column WIP limit
- [ ] Concrete values continue to set those fields
- [ ] The three-state deserializer is shared instead of copied across models/routes
- [ ] Users without a password hash fail password verification safely
- [ ] Server tests and Clippy pass

## Verification commands

```powershell
cargo test --manifest-path apps/server/Cargo.toml
cargo clippy --manifest-path apps/server/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - omit/clear/set semantics and nullable password handling are correct across all named resources.
- **partial** - the pattern works for some fields but coverage or auth compatibility is incomplete.
- **fail** - explicit null is still discarded, omission clears data, auth panics, or checks fail.

## Graders-only reference evidence

Run this cross-layer contract discriminator:

```powershell
$models = Get-Content apps/server/src/models/mod.rs -Raw
$board = Get-Content apps/server/src/models/board.rs -Raw
$sprint = Get-Content apps/server/src/models/sprint.rs -Raw
$user = Get-Content apps/server/src/models/user.rs -Raw
$auth = Get-Content apps/server/src/services/auth_service.rs -Raw
if (-not $models.Contains("pub fn double_option<'de, T, D>") -or -not $board.Contains('Option<Option<String>>') -or ([regex]::Matches($sprint, 'Option<Option<')).Count -lt 3 -or -not $user.Contains('pub password_hash: Option<String>') -or -not $auth.Contains('password_hash.as_deref().unwrap_or("")')) { exit 1 }
```

All five conditions fail at `f33a9b1b0ba544c8312d230367c0f521f5e11593`; they pass together at `4c1974b70eb8025882c1ebf5a9c5a97a10e8e839`.

The reference moves a reusable double-option deserializer into `models`, applies it to board/sprint/column payloads, uses outer-option unwrapping in services, and changes `User.password_hash` to `Option<String>`. Inspect with `git diff f33a9b1b0ba544c8312d230367c0f521f5e11593 4c1974b70eb8025882c1ebf5a9c5a97a10e8e839 -- apps/server/src`.
