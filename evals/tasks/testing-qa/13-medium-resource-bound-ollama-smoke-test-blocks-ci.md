# Task 13 - Resource-bound Ollama smoke test blocks CI

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `ee5f300bd8fc322977480bdaaef25603afde0591`
Start commit: `a1c17ad4bffef7420e5137d5bb0a160f2d0bc8d0`
Difficulty: **medium**
Category: CI integration policy

## Prompt (given to the agent verbatim)

The live Ollama smoke job uses a slow local model on a constrained runner. Valid long responses can exceed the client deadline, while intermittent model quality can block unrelated pull requests even though deterministic checks pass. Rebalance the client timeout, probe output budget, and CI gate policy without removing the live smoke test or weakening deterministic gates.

## Success criteria (checkable)

- [ ] Ollama client deadline covers cold load plus slow constrained-runner generation.
- [ ] Golden probe uses a smaller bounded output allowance.
- [ ] Live integration remains enabled and still performs schema validation.
- [ ] Integration failure is informational while lint, typecheck, and unit tests remain blocking.
- [ ] CI job retains its dependencies, overall timeout, diagnostics, and real Ollama service.

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib ollama
$provider = Get-Content apps/desktop/src-tauri/src/providers/llm/ollama.rs -Raw
$probe = Get-Content apps/desktop/src-tauri/src/services/ollama_probe_test_support.rs -Raw
$workflow = Get-Content .github/workflows/ci.yml -Raw
if ($provider -notmatch 'DEFAULT_TIMEOUT_SECONDS:\s*u64\s*=\s*600' -or $probe -notmatch 'max_tokens:\s*Some\(1_500\)' -or $workflow -notmatch '(?ms)integration-test:.*?continue-on-error:\s*true') { exit 1 }
# Secondary live smoke check when a local Ollama service is available:
if ($env:OLLAMA_INTEGRATION -eq '1') { pnpm --filter @testing-ide/desktop run test:integration }
```

## Scoring: pass / partial / fail notes

- **pass** - timeout, output budget, and non-blocking smoke policy are coherent while deterministic gates stay strict.
- **partial** - CI stops blocking but runtime bounds, diagnostics, or live validation are incomplete.
- **fail** - integration is removed/mocked, deterministic gates become optional, or slow valid calls still hit the old deadline.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet a1c17ad4bffef7420e5137d5bb0a160f2d0bc8d0 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference raises Ollama client timeout to 600 seconds, reduces only the golden probe output cap to 1500, and marks only the live integration job `continue-on-error`. Inspect with `git -C "C:\Testing IDE" show ee5f300bd8fc322977480bdaaef25603afde0591`.
