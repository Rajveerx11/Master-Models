# Task 19 - Provider and sandbox failures lose the real cause

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `1c0fd5ee372e1f8252df4ae099deab28880c5824`
Start commit: `a0e3d672415eea01ad27339cb66465cac87d0a84`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Improve failure handling across generation and sandbox execution. Some aggregating LLM endpoints return structured errors inside successful SSE transport; empty forced tool calls can create useless artifacts; and sandbox runs that collect zero tests persist no useful reason. Interpret those conditions into typed, actionable failures, attempt one schema-guided JSON fallback where appropriate, retain captured runner diagnostics, and prevent constrained containers from over-creating runtime threads.

## Success criteria (checkable)

- [ ] In-band provider errors map auth, rate-limit, timeout, and generic failures to existing typed errors
- [ ] Empty forced tool output triggers one non-tool JSON fallback with the expected schema instruction
- [ ] Empty or structurally empty artifact payloads are rejected with an actionable model hint
- [ ] Non-target artifact types are unaffected by specialized empty-payload checks
- [ ] Zero-test sandbox errors persist stderr, then stdout, then a deterministic placeholder
- [ ] Docker runners cap runtime thread creation consistently
- [ ] Unit/integration tests and strict Clippy pass

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib parse_inband
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib empty_forced_tool_call
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib run_with_zero_tests_persists_error_message_from_stderr
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - provider, generation, and sandbox failures retain correct typed meaning and useful diagnostics.
- **partial** - major cases improve but one mapping, fallback bound, validation, persistence, or container guard is missing.
- **fail** - failures remain silent/misclassified, retries can loop, empty artifacts persist, or checks fail.

## Graders-only reference evidence

Run these exact focused-test and container-policy discriminators:

```powershell
foreach ($case in @(@('parse_inband_', 3), @('empty_forced_tool_call_retries_without_tool_and_salvages_json', 1), @('run_with_zero_tests_persists_error_message_from_stderr', 1))) {
  $output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib $case[0] 2>&1
  $code = $LASTEXITCODE
  $output | Write-Output
  if ($code -ne 0 -or $output -notmatch ("{0} passed" -f $case[1])) { exit 1 }
}
$harness = Get-Content apps/desktop/src-tauri/src/providers/runners/docker_harness.rs -Raw
$runner = Get-Content apps/desktop/src-tauri/src/providers/runners/docker_js.rs -Raw
if (-not $harness.Contains('GOMAXPROCS={gomaxprocs}') -or -not $runner.Contains('--no-file-parallelism')) { exit 1 }
```

At `a0e3d672415eea01ad27339cb66465cac87d0a84`, the filters yield zero matching tests and both thread-cap markers are absent. At `1c0fd5ee372e1f8252df4ae099deab28880c5824`, the filters yield 3, 1, and 1 passing tests and both markers exist.

The reference adds in-band SSE error mapping, one-pass JSON fallback, artifact-specific empty guards, zero-test diagnostic persistence, thread caps, and focused tests across the provider, generation, runner, and sandbox service modules. Inspect with `git diff a0e3d672415eea01ad27339cb66465cac87d0a84 1c0fd5ee372e1f8252df4ae099deab28880c5824 -- apps/desktop/src-tauri/src/providers apps/desktop/src-tauri/src/services`.
