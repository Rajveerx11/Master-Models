# Task 03 - Valid Ollama response fails an accounting assertion

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `493bba4132f0a874cba3bc322c1f983d9b60af91`
Start commit: `6b1b066c9f1e614ede85b86482313ae03fed5723`
Difficulty: **easy**
Category: integration-test robustness

## Prompt (given to the agent verbatim)

The live Ollama round-trip can return a valid non-empty completion while reporting zero output tokens on some model/server combinations. The integration test currently treats that optional accounting field as the correctness signal. Preserve real response validation without failing successful generations solely because token usage is unavailable.

## Success criteria (checkable)

- [ ] Empty generated text still fails the round-trip test.
- [ ] A non-empty completion with zero reported output tokens no longer fails.
- [ ] Missing token accounting remains visible in test output for diagnosis.
- [ ] Provider production behavior is unchanged.

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --test integration_ollama --no-run
$source = Get-Content apps/desktop/src-tauri/tests/integration_ollama.rs -Raw
if ($source -match 'assert!\(\s*response\.usage\.output_tokens\s*>\s*0' -or $source -notmatch 'if\s+response\.usage\.output_tokens\s*==\s*0' -or $source -notmatch 'eprintln!') { exit 1 }
# Secondary live smoke check when explicitly enabled:
if ($env:OLLAMA_INTEGRATION -eq '1') { cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --test integration_ollama ollama_chat_generate_round_trip -- --nocapture }
```

## Scoring: pass / partial / fail notes

- **pass** - test validates the behavioral signal and treats accounting as diagnostic.
- **partial** - false failure removed but visibility or empty-response protection is lost.
- **fail** - valid calls still fail, or the test becomes effectively assertion-free.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 6b1b066c9f1e614ede85b86482313ae03fed5723 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference changes only `apps/desktop/src-tauri/tests/integration_ollama.rs`. Non-empty text remains mandatory; zero output tokens emit a warning instead of failing. Inspect with `git -C "C:\Testing IDE" show 493bba4132f0a874cba3bc322c1f983d9b60af91`.
