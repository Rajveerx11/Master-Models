# Task 06 - Hide password hashes from direct database clients

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `0bba169007718204cfb42662d554a99f5d89dbc3`
Start commit: `de8cd8a6e3749421002800e21d31db43e37d0cda`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Signed-in desktop clients need to read public user profiles directly, but the current row policy also lets them select every user's password hash. Restrict direct clients to the profile columns required by the application while preserving self-service profile creation and updates. Accounts backed only by the external authentication service must remain valid even though they have no local password hash.

## Success criteria (checkable)

- [ ] Authenticated direct clients cannot select the password-hash column for any user
- [ ] Authenticated clients retain only the profile-column select, insert, and update privileges needed by existing flows
- [ ] Anonymous and table-wide grants do not bypass the column restriction
- [ ] External-auth profile rows can store a null local password hash
- [ ] Row-level self-update and self-insert policies remain enforced

## Verification commands

```powershell
$init = Get-Content -LiteralPath apps/server/migrations/0001_boards_init.sql -Raw
$rls = Get-Content -LiteralPath apps/server/migrations/0002_boards_rls.sql -Raw
if ($init -match 'password_hash\s+TEXT\s+NOT NULL') { throw 'external-auth profiles still require a local password hash' }
if ($rls -notmatch 'REVOKE ALL ON users FROM anon, authenticated') { throw 'table-wide user grants were not revoked' }
$selectGrant = [regex]::Match($rls, '(?is)GRANT SELECT\s*\((?<columns>[^)]*)\)\s*ON users TO authenticated').Groups['columns'].Value
if (-not $selectGrant -or $selectGrant -match 'password_hash') { throw 'authenticated SELECT grant exposes password_hash' }
foreach ($column in @('id','email','display_name','avatar_url','created_at','updated_at')) { if ($selectGrant -notmatch "\b$column\b") { throw "profile SELECT grant omits $column" } }
if ($rls -notmatch '(?is)GRANT INSERT\s*\([^)]*\)\s*ON users TO authenticated' -or $rls -notmatch '(?is)GRANT UPDATE\s*\([^)]*\)\s*ON users TO authenticated') { throw 'self-service profile grants are missing' }
```

## Scoring: pass / partial / fail notes

- **pass** - column privileges hide hashes while required profile access and external-auth account creation continue to work.
- **partial** - hashes are hidden but a required profile operation breaks, or nullability is fixed without closing disclosure.
- **fail** - any authenticated direct client can still select password hashes, grants become broader, or external-auth registration remains invalid.

## Graders-only reference evidence

Reference solution: `git -C "C:\Testing IDE" show 0bba169007718204cfb42662d554a99f5d89dbc3` (graders only - never shown to a model).

The reference changes only the two board migrations. It makes `password_hash` nullable, revokes table-level access from `anon` and `authenticated`, and grants authenticated users only named public-profile columns for select plus narrow self-service insert/update columns. The content assertions fail on the start object and pass on the reference object.
