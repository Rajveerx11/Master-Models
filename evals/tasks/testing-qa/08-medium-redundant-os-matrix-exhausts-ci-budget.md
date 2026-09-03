# Task 08 - Redundant OS matrix exhausts CI budget

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `26371aeda9fafb12b6868364b2ee4f74f8fd54cd`
Start commit: `6112f8c17d0e94d466a0a9a36e5c7e7990fc09b7`
Difficulty: **medium**
Category: CI coverage optimization

## Prompt (given to the agent verbatim)

Every push runs lint, TypeScript checking, frontend unit tests, and Rust unit tests on Linux, Windows, and macOS. These checks do not exercise platform-specific behavior, but the matrix rapidly exhausts the private repository's free Actions allowance. Reduce billed work without losing the cross-platform packaging contract or changing required check names.

## Success criteria (checkable)

- [ ] Lint, typecheck, and unit-test jobs each run once on Ubuntu for pushes and pull requests.
- [ ] Their commands, frozen dependency installation, Rust checks, and Linux prerequisites remain intact.
- [ ] Required job names are exactly `lint`, `typecheck`, and `unit-test`.
- [ ] Windows, Linux, and macOS bundle coverage remains in the release workflow.
- [ ] No platform-specific product tests are silently deleted.
- [ ] Workflow syntax remains valid and concurrency behavior is unchanged.

## Verification commands

```powershell
$ci = Get-Content .github/workflows/ci.yml -Raw
function Get-JobBlock([string]$yaml, [string]$job) {
  $match = [regex]::Match($yaml, "(?ms)^  $([regex]::Escape($job)):\r?\n(?<body>.*?)(?=^  [A-Za-z0-9_-]+:\r?$|\z)")
  if (-not $match.Success) { throw "missing job: $job" }
  $match.Groups['body'].Value
}
foreach ($job in @('lint', 'typecheck', 'unit-test')) {
  $body = Get-JobBlock $ci $job
  if ($body -notmatch "(?m)^    name:\s*$([regex]::Escape($job))\s*$" -or $body -notmatch '(?m)^    runs-on:\s*ubuntu-latest\s*$') { throw "$job is not a stable Ubuntu-only required check" }
  if ($body -match 'matrix\.os|(?m)^    strategy:') { throw "$job still expands an OS matrix" }
  if ($body -notmatch 'pnpm install --frozen-lockfile') { throw "$job lost frozen dependency installation" }
}
$release = Get-Content .github/workflows/release.yml -Raw
foreach ($platform in @('ubuntu-latest', 'windows-latest', 'macos-latest')) { if ($release -notmatch [regex]::Escape($platform)) { throw "release matrix lost $platform" } }
if ($ci -notmatch '(?ms)^concurrency:.*?cancel-in-progress:\s*true') { throw 'CI concurrency cancellation changed' }
pnpm lint
pnpm typecheck
pnpm test
```

## Scoring: pass / partial / fail notes

- **pass** - redundant per-push OS expansion is removed while check identity, commands, and release matrix coverage remain.
- **partial** - billed work falls but names, commands, prerequisites, or release coverage drift.
- **fail** - tests are removed, platform release coverage disappears, or workflows become invalid.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 6112f8c17d0e94d466a0a9a36e5c7e7990fc09b7 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference changes only `.github/workflows/ci.yml`: three platform matrices become Ubuntu jobs, matrix suffixes leave job names, Linux guards become unnecessary, and all check commands remain. `release.yml` already retains the cross-platform bundle matrix. Inspect with `git -C "C:\Testing IDE" show 26371aeda9fafb12b6868364b2ee4f74f8fd54cd`.
