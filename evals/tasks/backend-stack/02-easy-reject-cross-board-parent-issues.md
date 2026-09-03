# Task 02 - Reject cross-board parent issues

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `d0f4c82fe408b3b31d93dcedd5430f13e887cf39`
Start commit: `ab7f4f2a586091ff9c30a2f7679a983628c229d6`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

Creating an issue accepts a parent issue from a different board. This creates an invalid hierarchy and can later delete work through the parent foreign key. Validate optional parent ownership before creating the issue. Preserve same-board parents and distinguish a missing parent from a parent owned by another board.

## Success criteria (checkable)

- [ ] An existing parent on the target board is accepted
- [ ] A parent on another board returns a validation error
- [ ] A missing parent returns a not-found error
- [ ] Validation happens before the issue counter or insert transaction is changed
- [ ] Server checking passes

## Verification commands

```powershell
cargo check --manifest-path apps/server/Cargo.toml
```

## Scoring: pass / partial / fail notes

- **pass** - issue creation enforces board ownership with distinct missing-parent behavior before mutation.
- **partial** - cross-board parents are blocked but error semantics or mutation ordering is wrong.
- **fail** - invalid parents remain accepted, valid parents break, or checking fails.

## Graders-only reference evidence

Run this source-contract discriminator:

```powershell
$source = Get-Content apps/server/src/services/issue_service.rs -Raw
$lookup = $source.IndexOf('SELECT board_id FROM issues WHERE id = $1')
$transaction = $source.IndexOf('let mut tx = pool.begin().await?')
if ($lookup -lt 0 -or $transaction -lt 0 -or $lookup -gt $transaction -or -not $source.Contains('parent issue does not belong to this board') -or -not $source.Contains('parent issue not found')) { exit 1 }
```

This exits `1` at `ab7f4f2a586091ff9c30a2f7679a983628c229d6` because all three parent-validation markers are absent, and exits `0` at `d0f4c82fe408b3b31d93dcedd5430f13e887cf39`.

The reference performs a scoped parent lookup before opening the transaction and maps absent versus foreign parents to different API errors. Inspect with `git diff ab7f4f2a586091ff9c30a2f7679a983628c229d6 d0f4c82fe408b3b31d93dcedd5430f13e887cf39 -- apps/server/src/services/issue_service.rs`.
