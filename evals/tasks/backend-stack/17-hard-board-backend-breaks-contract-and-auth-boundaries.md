# Task 17 - Board backend breaks contract and auth boundaries

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `33a61dfa8be6888ad0a612172dc89e1e5a7a457f`
Start commit: `c8ce0aa11c3b726087e1a7d47f1be0d92f0c09ee`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Harden the boards backend around update semantics, authorization state, and concurrent ordering. Clients must be able to clear nullable issue fields without activity logs disagreeing with persisted values. Issues must never move into a column from another board, a team must retain at least one admin, WebSocket credentials must not travel in URLs, request bodies must not be logged at normal verbosity, and deleting/reordering columns must respect the database uniqueness constraint.

## Success criteria (checkable)

- [ ] Issue updates distinguish omitted, explicit-null, and concrete nullable fields
- [ ] Activity records and the database update use one resolved set of effective values
- [ ] Moving an issue rejects a target column belonging to another board
- [ ] Demoting the last team admin is rejected consistently with member removal
- [ ] WebSockets authenticate with a bounded first message and acknowledge success; JWTs are absent from URLs
- [ ] Request-body logging is debug-only
- [ ] Column deletion/reordering avoids transient uniqueness conflicts
- [ ] Server tests and strict Clippy pass

## Verification commands

```powershell
cargo test --manifest-path apps/server/Cargo.toml
cargo clippy --manifest-path apps/server/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - every contract, authorization, logging, timeout, and ordering invariant is enforced.
- **partial** - most invariants hold but one failure path or consistency requirement remains.
- **fail** - cross-board moves, last-admin loss, URL credentials, stale logs, or constraint failures remain.

## Graders-only reference evidence

Run this invariant discriminator:

```powershell
$issueModel = Get-Content apps/server/src/models/issue.rs -Raw
$issueService = Get-Content apps/server/src/services/issue_service.rs -Raw
$teamService = Get-Content apps/server/src/services/team_service.rs -Raw
$ws = Get-Content apps/server/src/routes/ws.rs -Raw
$issuesRoute = Get-Content apps/server/src/routes/issues.rs -Raw
$boards = Get-Content apps/server/src/services/board_service.rs -Raw
$delete = $boards.IndexOf('DELETE FROM board_columns WHERE id = $1')
$shift = $boards.IndexOf('UPDATE board_columns SET position = position - 1')
if (-not $issueModel.Contains("fn double_option<'de, T, D>") -or -not $issueService.Contains('column does not belong to this board') -or -not $teamService.Contains('cannot demote the last admin of the team') -or -not $ws.Contains('const AUTH_TIMEOUT: Duration = Duration::from_secs(10)') -or -not $ws.Contains('{"type":"auth_ok"}') -or -not $issuesRoute.Contains('tracing::debug!("Raw request JSON payload') -or $delete -lt 0 -or $shift -lt 0 -or $delete -gt $shift) { exit 1 }
```

At `c8ce0aa11c3b726087e1a7d47f1be0d92f0c09ee`, every newly enforced marker is absent or ordered incorrectly; all checks pass at `33a61dfa8be6888ad0a612172dc89e1e5a7a457f`.

The reference changes issue update models/services, move validation, team-role guards, WebSocket first-message authentication with a ten-second timeout and acknowledgement, request logging level, and delete-before-shift ordering. Inspect with `git diff c8ce0aa11c3b726087e1a7d47f1be0d92f0c09ee 33a61dfa8be6888ad0a612172dc89e1e5a7a457f -- apps/server/src`.
