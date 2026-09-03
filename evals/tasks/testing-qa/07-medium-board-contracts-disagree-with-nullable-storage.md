# Task 07 - Board contracts disagree with nullable storage

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `9461860ba3d478078e8ab57caafe98ecb432c8b2`
Start commit: `ee984880f128119aec5ee6ae57a10b63cd391078`
Difficulty: **medium**
Category: schema and persistence contract tests

## Prompt (given to the agent verbatim)

Board data can legitimately contain null descriptions, sprint goals/dates, and activity-log before/after values because the database columns are nullable, but shared runtime schemas and TypeScript types reject those rows. Align the public contracts with storage, export the board schemas, and make multi-row column reordering transaction-safe. Add round-trip tests for nullable records.

## Success criteria (checkable)

- [ ] Shared board schemas are exported from the package entry point.
- [ ] Runtime schemas and plain TypeScript types agree on every nullable board field.
- [ ] Contract tests parse representative team, board, sprint, and activity-log rows containing null values.
- [ ] Column position uniqueness remains enforced at commit while allowing temporary conflicts during one reorder transaction.
- [ ] Non-null required identifiers and relationships remain strict.
- [ ] Shared tests and typecheck pass.

## Verification commands

```powershell
pnpm --filter @testing-ide/shared test
pnpm --filter @testing-ide/shared run typecheck
```

## Scoring: pass / partial / fail notes

- **pass** - storage, runtime schemas, static types, exports, migration semantics, and round-trip tests agree.
- **partial** - common null rows parse but one contract layer, export, test, or reorder constraint remains wrong.
- **fail** - nullable storage still fails validation, required fields become optional, or uniqueness is removed.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet ee984880f128119aec5ee6ae57a10b63cd391078 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference exports `board.schema`, makes only DB-nullable fields nullable/optional in Zod and TypeScript, adds four round-trip groups, and changes `(board_id, position)` uniqueness to `DEFERRABLE INITIALLY DEFERRED`. Inspect with `git -C "C:\Testing IDE" show 9461860ba3d478078e8ab57caafe98ecb432c8b2`.
