# Task 14 - Enforce layered push and merge guards

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `b51b65242dd7a9b38a487d9753fdfdf7b6bb0e71`
Start commit: `0d778ffce0ea991fc86ea1aa8339ee0f4d9eb2f9`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

The repository relies on contributors remembering every safety check before pushing, and protected-branch expectations are undocumented. Add one coherent guardrail workflow: fast commit-time checks must reject unresolved conflict markers and accidentally staged files larger than 5 MiB; push-time checks must run the repository's full local quality gate; and pull requests may opt into native auto-merge only after normal review and required checks pass. Wire hooks through the existing package manager and document the exact branch-protection settings administrators must enable. Do not create any path that bypasses GitHub protection.

## Success criteria (checkable)

- [ ] A fast pre-commit hook rejects real conflict-marker lines and staged files over 5 MiB with actionable errors
- [ ] A pre-push hook delegates to one maintained script that runs typecheck, lint, frontend tests, Rust formatting, Clippy, and Rust tests with fail-fast behavior
- [ ] Hook installation is wired into dependency setup without breaking environments where Git hooks are unavailable
- [ ] Auto-merge is opt-in, ignores draft pull requests, uses squash mode, and still depends on branch protection, review, and required checks
- [ ] CODEOWNERS, pull-request guidance, contributor docs, and branch-protection instructions agree on the same workflow

## Verification commands

```powershell
pnpm guard:markers
$scripts = @('.husky/pre-commit', '.husky/pre-push', 'tools/scripts/pre-push.sh')
foreach ($script in $scripts) {
  (Get-Content -LiteralPath $script -Raw).Replace("`r", '') | bash -n
  if ($LASTEXITCODE -ne 0) { throw "$script has invalid shell syntax" }
}
$probe = '.security-eval-over-5mib.bin'
$normalizedPaths = @('.husky/pre-commit', 'tools/scripts/pre-push-no-markers.sh')
$originalBytes = @{}; foreach ($path in $normalizedPaths) { $originalBytes[$path] = [IO.File]::ReadAllBytes((Join-Path (Get-Location) $path)) }
$oldGitDir = $env:GIT_DIR; $oldGitWorkTree = $env:GIT_WORK_TREE
try {
  foreach ($path in $normalizedPaths) {
    $text = (Get-Content -LiteralPath $path -Raw).Replace("`r", '')
    [IO.File]::WriteAllText((Join-Path (Get-Location) $path), $text, [Text.UTF8Encoding]::new($false))
  }
  $env:GIT_DIR = (git rev-parse --absolute-git-dir)
  $env:GIT_WORK_TREE = (git rev-parse --show-toplevel)
  [IO.File]::WriteAllBytes((Join-Path (Get-Location) $probe), [byte[]]::new(5242881))
  git add -- $probe
  if ($LASTEXITCODE -ne 0) { throw 'could not stage oversized probe' }
  $guardOutput = @(& bash .husky/pre-commit 2>&1)
  if ($LASTEXITCODE -eq 0) { throw 'pre-commit accepted a staged file larger than 5 MiB' }
  if (($guardOutput -join "`n") -notmatch 'larger than 5 MB|5 MiB') { throw 'guard failure was not the staged-file size check' }
} finally {
  git restore --staged -- $probe 2>$null
  Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
  foreach ($path in $normalizedPaths) { [IO.File]::WriteAllBytes((Join-Path (Get-Location) $path), $originalBytes[$path]) }
  $env:GIT_DIR = $oldGitDir; $env:GIT_WORK_TREE = $oldGitWorkTree
}
if (Get-Command actionlint -ErrorAction SilentlyContinue) { actionlint .github/workflows/auto-merge.yml; if ($LASTEXITCODE -ne 0) { throw 'actionlint failed' } }
```

## Scoring: pass / partial / fail notes

- **pass** - local hooks, the shared push gate, opt-in auto-merge, and administrator documentation form one consistent protected-branch workflow.
- **partial** - the main gates work but one hook, CI condition, ownership rule, or documented protection setting is incomplete.
- **fail** - conflict markers or huge staged files pass silently, the quality gate is bypassed, auto-merge weakens protection, or scripts/workflow syntax is invalid.

## Graders-only reference evidence

Reference solution: `git -C "C:\Testing IDE" show b51b65242dd7a9b38a487d9753fdfdf7b6bb0e71` (graders only - never shown to a model).

The reference adds a fast pre-commit marker/5 MiB guard, a pre-push wrapper around one full-check script, Husky setup, CODEOWNERS and pull-request guidance, explicit branch-protection instructions, and an opt-in non-draft auto-merge workflow that invokes GitHub native auto-merge rather than bypassing required checks.
