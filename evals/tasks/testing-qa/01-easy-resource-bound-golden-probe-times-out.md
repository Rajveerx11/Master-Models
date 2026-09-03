# Task 01 - Resource-bound golden probe times out

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `60b6a382cf732b50b0e0100e69abcaee59cb4fed`
Start commit: `ac52d3a48d8971f689662a74030f347d29245ddb`
Difficulty: **easy**
Category: integration configuration

## Prompt (given to the agent verbatim)

The live golden probe repeatedly reaches its per-attempt timeout on a free CI runner because its chat model generates the maximum structured response too slowly. Select a smaller compatible chat model for this resource-bound job and keep every pull, warmup, frontend-test, and Rust-test reference consistent. Do not reduce context, output allowance, retries, or schema checks.

## Success criteria (checkable)

- [ ] CI uses the same smaller chat model when pulling, warming, and running both integration suites.
- [ ] The embedding model and two-model residency setup remain unchanged.
- [ ] Context length, response token allowance, per-attempt timeout, retries, and schema validation remain unchanged.
- [ ] Comments accurately describe the selected model and runner limits.
- [ ] Integration remains opt-in/non-blocking rather than being removed or mocked.

## Verification commands

```powershell
$env:OLLAMA_BASE_URL='http://127.0.0.1:11434'
$env:OLLAMA_TEST_CHAT_MODEL='qwen2.5-coder:1.5b'
$env:OLLAMA_TEST_EMBED_MODEL='nomic-embed-text'
pnpm --filter @testing-ide/desktop run test:integration
$env:OLLAMA_INTEGRATION='1'
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --test integration_ollama -- --nocapture
```

## Scoring: pass / partial / fail notes

- **pass** - all integration job references use one faster compatible model and no validation budget is weakened.
- **partial** - runtime improves but model references drift or another correctness control changes.
- **fail** - timeout persists, tests are skipped/mocked, or context/output/schema coverage is reduced.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet ac52d3a48d8971f689662a74030f347d29245ddb -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference changes only `.github/workflows/ci.yml`, replacing every golden chat-model occurrence with `qwen2.5-coder:1.5b` and updating model-size comments while retaining context, output, retry, timeout, embedding, and validation settings. Inspect with `git -C "C:\Testing IDE" show 60b6a382cf732b50b0e0100e69abcaee59cb4fed`.
