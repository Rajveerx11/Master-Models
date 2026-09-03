# Task 10 - CI has no actionable coverage report

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `51e5d117fc15914b499eb61e3b513782ede5fa8a`
Start commit: `1f8aed9327de77c06afe0bd323ec2d91a01407bb`
Difficulty: **medium**
Category: coverage infrastructure

## Prompt (given to the agent verbatim)

CI runs frontend and Rust tests but gives no coverage visibility for the service and utility layers. Add reproducible LCOV reporting for both stacks, upload the reports together, and keep coverage informational until the project has enough baseline data for a stable threshold.

## Success criteria (checkable)

- [ ] Frontend coverage uses Vitest's V8 provider and emits text plus LCOV.
- [ ] Frontend measurement targets utility/store code and excludes tests and integration specs.
- [ ] Rust library coverage emits LCOV with the locked dependency graph.
- [ ] CI uploads both expected report paths under one artifact.
- [ ] Coverage tooling failures do not block unrelated pull requests.
- [ ] Local commands are documented and lockfile changes are consistent.

## Verification commands

```powershell
pnpm --filter @testing-ide/desktop run test:coverage
cargo llvm-cov --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib --lcov --output-path apps/desktop/src-tauri/lcov.info
```

## Scoring: pass / partial / fail notes

- **pass** - both LCOV reports are generated and published with correct scope and non-blocking CI semantics.
- **partial** - only one stack works, paths mismatch, or measurement includes misleading surfaces.
- **fail** - no usable artifacts, tests are skipped, or coverage becomes an unjustified hard gate.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 1f8aed9327de77c06afe0bd323ec2d91a01407bb -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference adds a `coverage` job, V8 configuration and dependency, a `test:coverage` script, LCOV upload paths, and contributor instructions. Inspect with `git -C "C:\Testing IDE" show 51e5d117fc15914b499eb61e3b513782ede5fa8a`.
