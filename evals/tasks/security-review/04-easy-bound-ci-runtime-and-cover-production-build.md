# Task 04 - Bound CI runtime and cover production build

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `59dc9d449f35b75fb3e968566bfbc1d2c87ad849`
Start commit: `c70a88d298f4cb16a8ea2a38355b3df7a7ea9b0d`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

Repository workflows can run for the platform default when a job hangs, and pull requests do not exercise the production renderer bundle before release. Put reasonable explicit limits on every job, add a lightweight production-build gate, and allow operators to rerun CI and release workflows manually. Preserve existing triggers, permissions, and release behavior.

## Success criteria (checkable)

- [ ] Every CI, release, and auto-merge job has an explicit timeout appropriate to its workload
- [ ] Pull requests run the desktop renderer's production Vite build after a frozen dependency install
- [ ] CI and release workflows support manual dispatch without removing current push, PR, or tag triggers
- [ ] Workflow permissions and release matrix remain unchanged except where required by the new checks

## Verification commands

```powershell
$workflowPaths = @('.github/workflows/ci.yml', '.github/workflows/release.yml', '.github/workflows/auto-merge.yml')
$workflows = @{}; foreach ($path in $workflowPaths) { $workflows[$path] = Get-Content -LiteralPath $path -Raw }
foreach ($path in $workflowPaths) {
  $jobCount = ([regex]::Matches($workflows[$path], '(?m)^    runs-on:')).Count
  $timeoutCount = ([regex]::Matches($workflows[$path], '(?m)^    timeout-minutes: [1-9][0-9]*$')).Count
  if ($jobCount -eq 0 -or $timeoutCount -ne $jobCount) { throw "$path does not bound every job" }
}
foreach ($path in @('.github/workflows/ci.yml', '.github/workflows/release.yml')) {
  if ($workflows[$path] -notmatch '(?m)^  workflow_dispatch:\s*$') { throw "$path lacks workflow_dispatch" }
}
$buildJob = [regex]::Match($workflows['.github/workflows/ci.yml'], '(?ms)^  build-check:\s*$.*?(?=^  [a-zA-Z0-9_-]+:\s*$|\z)').Value
if ($buildJob -notmatch 'pnpm install --frozen-lockfile' -or $buildJob -notmatch 'pnpm --filter @testing-ide/desktop run vite:build') { throw 'production build job is incomplete' }
if (Get-Command actionlint -ErrorAction SilentlyContinue) { actionlint @workflowPaths; if ($LASTEXITCODE -ne 0) { throw 'actionlint failed' } }
```

## Scoring: pass / partial / fail notes

- **pass** - all jobs are bounded, production bundle is gated, and workflow semantics remain intact.
- **partial** - core timeout or build coverage exists but one workflow or trigger is missed.
- **fail** - jobs remain unbounded, workflow YAML is invalid, or release behavior is weakened.

## Graders-only reference evidence

Reference solution: `git -C "C:\Testing IDE" show 59dc9d449f35b75fb3e968566bfbc1d2c87ad849` (graders only - never shown to a model).

The reference changes only three workflow files, adds per-job `timeout-minutes`, a renderer `build-check`, and `workflow_dispatch` on CI and release.
