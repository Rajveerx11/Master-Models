# Task 20 - Run a bounded survivor-guided improvement loop

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `6cdbc5b3b0e0432f328451f949e5ab12c9d83fac`
Start commit: `6e73ec9fff4d80502fe8f4600e365d3c2120f6d9`
Difficulty: **hard**
Category: mutation-guided QA loop

## Prompt (given to the agent verbatim)

Add a bounded service loop that uses surviving mutants as evidence for improving generated tests. Survivor feedback must identify location and operator-specific testing guidance within strict size limits. Each attempt must generate a descendant artifact, rescore it, keep the best non-regressing result, emit progress, and return the best known evidence when generation or scoring fails.

## Success criteria (checkable)

- [ ] Survivor feedback contains file, line, mutation evidence, and operator-specific guidance
- [ ] Feedback caps both survivor count and total content while summarizing omissions
- [ ] A perfect initial score returns without regeneration
- [ ] Regenerated tests form an artifact parent chain and each valid attempt is rescored
- [ ] Best selection never regresses when a later score is worse
- [ ] The loop stops on perfection, attempt exhaustion, cancellation, or unrecoverable failure
- [ ] Error results preserve the best artifact and score reached so far
- [ ] Mock-provider and mock-runner tests cover progress, red baselines, errored mutants, improvement, and regeneration failure

## Verification commands

```powershell
$feedback = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib synth_survivor_feedback 2>&1; $feedbackCode = $LASTEXITCODE; $feedback | Write-Output; if ($feedbackCode -ne 0 -or $feedback -notmatch '2 passed') { exit 1 }
$loop = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib improve_ 2>&1; $loopCode = $LASTEXITCODE; $loop | Write-Output; if ($loopCode -ne 0 -or $loop -notmatch '[1-9][0-9]* passed') { exit 1 }
```

## Scoring: pass / partial / fail notes

- **pass** - bounded evidence drives a tested, cancellable, non-regressing loop that preserves partial value on failure.
- **partial** - improvement works but bounds, versioning, best selection, progress, or partial-error results are incomplete.
- **fail** - loop is unbounded, overwrites artifacts, fabricates scores, regresses the best result, or tests fail.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 6e73ec9fff4d80502fe8f4600e365d3c2120f6d9 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference slice is the improvement logic and mock-backed tests added to `mutation_service.rs`; UI, IPC, store, schemas, and docs are outside this task's scoring scope. Inspect with `git diff 6e73ec9fff4d80502fe8f4600e365d3c2120f6d9 6cdbc5b3b0e0432f328451f949e5ab12c9d83fac -- apps/desktop/src-tauri/src/services/mutation_service.rs`.
