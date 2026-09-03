# Task 19 - Enforce team isolation in board database

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `09232b56d9675530ab5cdb5b01d2b985f3bbd5f8`
Start commit: `1ba7b26e1147839453bb8a08aba81377abd2775c`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

The desktop client queries board tables directly with a signed-in user's JWT, but the database does not isolate teams. Add row-level access control for every board-domain table using membership roles, while avoiding recursive policy checks. Provide narrowly granted atomic operations for joining by invite, moving issues, and starting sprints. Also prevent account deletion from cascading through teams and make sprint-completion columns explicit.

## Success criteria (checkable)

- [ ] Row-level security is enabled on all board-domain tables with member, writer, admin, author, and self rules matching each operation
- [ ] Security-definer functions fix their search path and enforce authorization internally; externally callable mutation RPCs are executable only by authenticated users
- [ ] Invite join, issue move, and sprint start validate ownership/team relationships and perform race-sensitive updates atomically
- [ ] Team creator deletion is restricted and completed-work semantics use an explicit column flag exposed in shared schema/types
- [ ] SQL is syntactically coherent and server/shared checks pass

## Verification commands

```powershell
cargo test --manifest-path apps/server/Cargo.toml
pnpm --filter @testing-ide/shared test
pnpm --filter @testing-ide/shared typecheck
docker version
# Required integration verification: execute every step in the disposable
# PostgreSQL plan below and retain its psql transcript. A skipped assertion,
# SQL error, or unavailable Docker daemon fails this hard task.
```

## Ephemeral Postgres/Supabase verification plan

Run the database checks against a disposable PostgreSQL 16 container or a fresh `supabase start` project, never a developer database:

1. Start a uniquely named PostgreSQL 16 container with a new anonymous volume. As its superuser, create `authenticated` and `anon` as `NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS` roles. Create schema `auth`, revoke its default `PUBLIC` access, and define `auth.uid()` as a stable SQL function returning `nullif(current_setting('request.jwt.claim.sub', true), '')::uuid`. Grant `USAGE` on schemas `auth` and `public`, plus `EXECUTE` on `auth.uid()`, to `authenticated`.
2. Apply `apps/server/migrations/0001_boards_init.sql` and `0002_boards_rls.sql` through `psql -X -v ON_ERROR_STOP=1`. Then grant `SELECT, INSERT, UPDATE, DELETE` on `teams`, `team_members`, `boards`, `board_columns`, `sprints`, `issues`, `comments`, `activity_logs`, `labels`, and `issue_labels` to `authenticated`. Do not grant table-wide access on `users`; retain the migration's column-level profile grants so `password_hash` remains inaccessible. These harness grants are required before `SET ROLE authenticated`, otherwise PostgreSQL stops at table permissions and never evaluates RLS.
3. As the database owner, seed two users, two unrelated teams, member/admin/viewer rows, boards, columns, sprints, issues, comments, labels, and activity rows. Switch to `SET ROLE authenticated` and set each simulated JWT subject with `select set_config('request.jwt.claim.sub', '<user-uuid>', true)` before assertions.
4. Prove the matrix: a member can read only their team's rows; a viewer cannot write; a member can perform writer operations but not admin operations; an outsider reads zero rows and cannot mutate; an author may change only their permitted records; self-service membership cannot insert another user.
5. Exercise each security-definer RPC with positive and negative cases: invite join accepts only the caller, issue move rejects cross-board relationships, and sprint start rejects non-writers and leaves exactly one active sprint. Launch two independent `psql` sessions against the sprint RPC and assert only one conflicting start succeeds.
6. Query `pg_proc.proconfig` to prove every security-definer function fixes `search_path`. Query `information_schema.routine_privileges` for `join_team_with_code`, `move_issue_on_board`, and `start_sprint_atomic` to prove `PUBLIC` and `anon` lack execute while `authenticated` has it. Query `pg_class.relrowsecurity` to prove all eleven board-domain tables have RLS enabled.
7. Stop the container and delete its anonymous volume in a `finally` block, even after a failed assertion.

## Scoring: pass / partial / fail notes

- **pass** - policies and helper functions enforce end-to-end tenant isolation with correct grants and atomicity.
- **partial** - common reads/writes isolate teams but a table, role, helper grant, relationship, or race remains weak.
- **fail** - signed-in users can cross team boundaries, definer functions bypass authorization, migrations fail, or checks fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\Testing IDE" show 09232b56d9675530ab5cdb5b01d2b985f3bbd5f8` (graders only - never shown to a model).

The reference adds a 375-line RLS migration covering eleven tables, fixed-search-path helper functions, authenticated-only RPC grants, row locking, FK hardening, and shared `isDone` data shape.
