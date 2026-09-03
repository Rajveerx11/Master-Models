# Task 03 - Document only reachable RustSec risk

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `aeeb099107366775c862ebfe21e50aee6d1c87cc`
Start commit: `667ae66fd04e30fa5fa988b1a27a0b44920e9667`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

Dependency audit reports several RustSec entries, but some belong only to unused database drivers, release-disabled behavior, or transitive desktop bindings. Add a single audit record that identifies every accepted advisory, explains whether its affected path is reachable here, states why an immediate upgrade is unsafe or unavailable, and gives a concrete review trigger. Do not claim that a finding is exploitable merely because it appears in the dependency graph.

## Success criteria (checkable)

- [ ] Every accepted advisory has an identifier, reachability rationale, and follow-up trigger
- [ ] Vulnerability entries are separated from unmaintained-crate warnings
- [ ] Rationales match this repository's SQLite-only and Tauri dependency usage
- [ ] No source code, lockfile, or dependency version is changed for a documentation-only triage task

## Verification commands

```powershell
$path = 'apps/desktop/src-tauri/audit.toml'
if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'audit.toml was not created' }
$changed = @(git status --porcelain=v1 --untracked-files=all | ForEach-Object { $_.Substring(3) })
if ($changed.Count -ne 1 -or $changed[0] -ne $path) { throw 'audit task changed files outside audit.toml' }
$record = Get-Content -LiteralPath $path -Raw
$ids = [regex]::Matches($record, '"RUSTSEC-[0-9]{4}-[0-9]{4}"') | ForEach-Object Value | Sort-Object -Unique
if ($ids.Count -ne 21) { throw "expected 21 accepted advisory IDs, found $($ids.Count)" }
foreach ($id in @('RUSTSEC-2025-0009', 'RUSTSEC-2023-0071', 'RUSTSEC-2024-0363')) {
  if ($record -notmatch [regex]::Escape($id)) { throw "missing $id" }
}
if (([regex]::Matches($record, '(?m)^# Triage:')).Count -ne 3) { throw 'each vulnerability needs a triage record' }
if (([regex]::Matches($record, '(?m)^# Action:')).Count -ne 3) { throw 'each vulnerability needs a review trigger' }
if ($record -notmatch 'VULNERABILITIES' -or $record -notmatch 'UNMAINTAINED') { throw 'risk classes are not separated' }
```

## Scoring: pass / partial / fail notes

- **pass** - complete, evidence-based triage documents accepted risk without severity inflation.
- **partial** - advisories are listed but reachability or review triggers are vague.
- **fail** - findings are blindly suppressed, risk is falsely dismissed, or unrelated dependencies change.

## Graders-only reference evidence

Reference solution: `git -C "C:\Testing IDE" show aeeb099107366775c862ebfe21e50aee6d1c87cc` (graders only - never shown to a model).

The reference creates only `apps/desktop/src-tauri/audit.toml`, separating three vulnerability decisions from transitive unmaintained warnings with explicit re-review conditions.

Reference discriminator: `git show 667ae66fd04e30fa5fa988b1a27a0b44920e9667:apps/desktop/src-tauri/audit.toml` fails because the file is absent, while `git show aeeb099107366775c862ebfe21e50aee6d1c87cc:apps/desktop/src-tauri/audit.toml` returns the record that satisfies all content assertions above. This proves the check fails at the start object and passes at the reference object without relying on staging.
