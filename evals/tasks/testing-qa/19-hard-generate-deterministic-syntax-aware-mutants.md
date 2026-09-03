# Task 19 - Generate deterministic syntax-aware mutants

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `48266fa55f46fff88a966aecf88c0b437e1c5704`
Start commit: `7e960ef6f41aceb296adf80f6ba536545d60af78`
Difficulty: **hard**
Category: mutation-engine verification

## Prompt (given to the agent verbatim)

Build a deterministic mutation engine for covered JavaScript and TypeScript source. Generate syntax-node mutations for arithmetic, comparison, logical, boolean, and return expressions; never mutate comments, strings, uncovered lines, or unsupported languages. Applying a mutation must splice the intended byte range safely, and a configured cap must sample repeatably while reporting omitted candidates.

## Success criteria (checkable)

- [ ] Arithmetic mutations cycle through distinct alternatives instead of producing the original operator
- [ ] Comparison, logical, boolean, and return mutations target syntax nodes accurately
- [ ] Comments and string contents never become mutation candidates
- [ ] Only covered source lines are eligible
- [ ] Applying a valid mutant changes exactly its byte range; invalid ranges are safe no-ops
- [ ] Unsupported languages and empty sources return no mutants
- [ ] Capped sampling is deterministic and reports the dropped count
- [ ] Pure engine tests require no sandbox, database, UI, or network
- [ ] The engine module is registered in the runner module tree

## Verification commands

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib providers::runners::mutation::tests 2>&1; $code = $LASTEXITCODE; $output | Write-Output; if ($code -ne 0 -or $output -notmatch '16 passed') { exit 1 }
```

## Scoring: pass / partial / fail notes

- **pass** - syntax-aware generation and application cover every operator family with deterministic bounds and sampling.
- **partial** - common operators work but syntax safety, coverage gating, byte splicing, or deterministic caps have gaps.
- **fail** - text replacement mutates comments/strings, candidates escape coverage, sampling varies, or tests fail.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 7e960ef6f41aceb296adf80f6ba536545d60af78 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference slice is `apps/desktop/src-tauri/src/providers/runners/mutation.rs` plus its `pub mod mutation;` registration in `runners/mod.rs`, containing the engine and sixteen pure tests. Inspect with `git diff 7e960ef6f41aceb296adf80f6ba536545d60af78 48266fa55f46fff88a966aecf88c0b437e1c5704 -- apps/desktop/src-tauri/src/providers/runners/mutation.rs apps/desktop/src-tauri/src/providers/runners/mod.rs`.
