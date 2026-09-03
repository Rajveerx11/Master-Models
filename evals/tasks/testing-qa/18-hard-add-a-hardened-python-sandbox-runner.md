# Task 18 - Add a hardened Python sandbox runner

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `f326b9bcb4b7fd3443ada42317d28822bff6b182`
Start commit: `7010eb762a0cf77304bf04731ca63141fe03bd1d`
Difficulty: **hard**
Category: cross-language result parsing

## Prompt (given to the agent verbatim)

Add a Python sandbox runner behind the existing runner abstraction. Share the hardened Docker workspace and execution machinery with the JavaScript runner, register language selection and service wiring, and convert pytest JSON reports plus coverage.py JSON into the existing typed contracts. Treat report files as untrusted container output: reject malformed JSON, bound attacker-controlled strings, map setup errors and source locations correctly, and keep parser and wiring tests independent of Docker.

## Success criteria (checkable)

- [ ] Passed, failed, skipped, and setup-error outcomes map to existing result statuses
- [ ] Test names, durations, failure messages, files, and source lines are preserved within bounds
- [ ] Generated case identifiers receive stable display normalization
- [ ] Executed and missing coverage lines map to deterministic hit counts
- [ ] Malformed reports return typed parse errors without panics
- [ ] Oversized attacker-controlled fields are capped before entering result contracts
- [ ] Python files select a registered Python runner while mixed Python/JS workspaces fail clearly
- [ ] JavaScript and Python runners share the same bounded, network-disabled, read-only Docker harness
- [ ] Fixture-backed parser and wiring tests run without Docker or network access
- [ ] Real container execution remains an optional secondary check

## Verification commands

```powershell
$pytest = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib parse_pytest_results 2>&1; $pytestCode = $LASTEXITCODE; $pytest | Write-Output; if ($pytestCode -ne 0 -or $pytest -notmatch '5 passed') { exit 1 }
$coverage = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib parse_coverage_py 2>&1; $coverageCode = $LASTEXITCODE; $coverage | Write-Output; if ($coverageCode -ne 0 -or $coverage -notmatch '3 passed') { exit 1 }
$harness = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib docker_harness::tests 2>&1; $harnessCode = $LASTEXITCODE; $harness | Write-Output; if ($harnessCode -ne 0 -or $harness -notmatch '7 passed') { exit 1 }
$factory = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib factory_maps_languages_to_their_runners 2>&1; $factoryCode = $LASTEXITCODE; $factory | Write-Output; if ($factoryCode -ne 0 -or $factory -notmatch '1 passed') { exit 1 }
$routing = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib detect_language_maps_extensions_and_rejects_mixed 2>&1; $routingCode = $LASTEXITCODE; $routing | Write-Output; if ($routingCode -ne 0 -or $routing -notmatch '1 passed') { exit 1 }
# Secondary environment check when explicitly enabled:
if ($env:DOCKER_INTEGRATION -eq '1') { cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib -- --ignored docker_py_runner_executes_a_real_suite }
```

## Scoring: pass / partial / fail notes

- **pass** - shared harness, language routing, and both parsers form a compileable, safely bounded Python runner with deterministic tests.
- **partial** - parsing works but harness reuse, registration, routing, bounds, or one report edge is incomplete.
- **fail** - Python is not wired through the runner abstraction, reports trust hostile output, primary checks require Docker, or focused tests fail.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 7010eb762a0cf77304bf04731ca63141fe03bd1d -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

The evaluated reference slice includes `commands/sandbox.rs`, `providers/runners/{docker_harness,docker_js,docker_py,factory,mod}.rs`, the two report fixtures, and `services/sandbox_service.rs`. Together they compile from the start state, register Python selection, reuse one hardened Docker harness, route the service by language, and provide deterministic parser and wiring tests; Docker execution remains ignored by default. Inspect with `git diff 7010eb762a0cf77304bf04731ca63141fe03bd1d f326b9bcb4b7fd3443ada42317d28822bff6b182 -- apps/desktop/src-tauri/src/commands/sandbox.rs apps/desktop/src-tauri/src/providers/runners apps/desktop/src-tauri/src/services/sandbox_service.rs`.
