# Task 14 - Health check hides runtime version drift

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `e4beadac7cf09a6aded5fbe74f0852a965413ee7`
Start commit: `9088795abd04335af81ee8de28b86e4a08595c25`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

The harness health panel only checks that Pi exists, so an incompatible installed version appears healthy. Introduce a versioned runtime contract, validate it strictly, compare installed and required versions, fail closed when the contract is invalid or absent, and show an actionable repair command. The degraded health layout must remain readable from very narrow to wide terminals and stay inside its ten-line budget.

## Success criteria (checkable)

- [ ] One checked-in runtime contract is the version source of truth
- [ ] Contract parsing requires the expected numeric schema and a valid semantic version string
- [ ] Missing, mismatched, matching, and missing-contract states are distinct and actionable
- [ ] Overall health is degraded when runtime validation fails
- [ ] Installed and required versions plus the full primary repair action remain visible at supported widths
- [ ] Degraded output never exceeds ten lines
- [ ] Harness verification passes

## Verification commands

```powershell
node scripts/verify-harness.mjs
node scripts/check-docs.mjs
```

## Scoring: pass / partial / fail notes

- **pass** - strict contract validation drives health state and responsive diagnostics without truncating the action.
- **partial** - drift is detected but contract validation, repair guidance, or narrow layout is incomplete.
- **fail** - incompatible runtime still reports healthy, malformed contracts pass, or checks fail.

## Graders-only reference evidence

Run this runtime-contract discriminator before the normal harness checks:

```powershell
$contractPath = 'agent/neura/runtime-contract.json'
if (-not (Test-Path $contractPath)) { exit 1 }
$contract = Get-Content $contractPath -Raw | ConvertFrom-Json
$health = Get-Content agent/extensions/harness-health.ts -Raw
$verify = Get-Content scripts/verify-harness.mjs -Raw
if ($contract.schemaVersion -ne 1 -or $contract.piVersion -notmatch '^\d+\.\d+\.\d+$' -or -not $health.Contains('export function parseRuntimeContract') -or -not $health.Contains('export function piRuntimeStatus') -or -not $verify.Contains('runtime-contract.json') -or -not $verify.Contains('repairAction')) { exit 1 }
```

The contract file and all parser/assertion markers are absent at `9088795abd04335af81ee8de28b86e4a08595c25`; they pass at `e4beadac7cf09a6aded5fbe74f0852a965413ee7`.

The reference adds `agent/neura/runtime-contract.json`, strict parsing and runtime status helpers, health-state integration, responsive ten-line rendering, installer synchronization, and deterministic harness assertions across widths. Inspect with `git diff 9088795abd04335af81ee8de28b86e4a08595c25 e4beadac7cf09a6aded5fbe74f0852a965413ee7 -- agent/extensions/harness-health.ts agent/neura/runtime-contract.json install.ps1 scripts/verify-harness.mjs scripts/check-docs.mjs`.
