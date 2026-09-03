# Task 06 - Ollama model eviction breaks integration runs

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `7b1983629de2742dda588f0d27362288ad9ebcac`
Start commit: `ce180221c0b9155883447b80d7ae6a17ab15ea43`
Difficulty: **medium**
Category: CI integration reliability

## Prompt (given to the agent verbatim)

The integration job loads an embedding model after the chat model. On constrained runners, Ollama evicts the first model; the next chat request pays a cold reload and exceeds the client's timeout. Make the suite reliable while still testing both real models and retaining useful failure diagnostics.

## Success criteria (checkable)

- [ ] CI keeps both integration models resident for the suite when capacity permits.
- [ ] Both models are explicitly warmed after download.
- [ ] Warmup requests have bounded timeouts and fail the setup step on errors.
- [ ] The Rust Ollama client tolerates a realistic constrained-runner cold load.
- [ ] Existing frontend and Rust integration suites still run with failure logs preserved.

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib ollama
$provider = Get-Content apps/desktop/src-tauri/src/providers/llm/ollama.rs -Raw
$workflow = Get-Content .github/workflows/ci.yml -Raw
if ($provider -notmatch 'DEFAULT_TIMEOUT_SECONDS:\s*u64\s*=\s*300' -or $workflow -notmatch 'OLLAMA_MAX_LOADED_MODELS:\s*"2"' -or $workflow -notmatch 'OLLAMA_KEEP_ALIVE:\s*"30m"' -or $workflow -notmatch 'Warm up Ollama models' -or $workflow -notmatch '/api/generate' -or $workflow -notmatch '/api/embeddings') { exit 1 }
# Secondary live smoke checks when explicitly enabled:
if ($env:OLLAMA_INTEGRATION -eq '1') { pnpm --filter @testing-ide/desktop run test:integration; cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --test integration_ollama -- --nocapture }
```

## Scoring: pass / partial / fail notes

- **pass** - model residency, warmup, and client timeout address the cold-load race coherently.
- **partial** - only one layer is changed or diagnostics/model coverage regress.
- **fail** - tests are disabled, models are removed, or cold reloads still exceed the client.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet ce180221c0b9155883447b80d7ae6a17ab15ea43 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference updates `.github/workflows/ci.yml` with two loaded models, a 30-minute keep-alive, single parallel request, and bounded chat/embedding warmups; `apps/desktop/src-tauri/src/providers/llm/ollama.rs` raises the client timeout from 120 to 300 seconds. Inspect with `git -C "C:\Testing IDE" show 7b1983629de2742dda588f0d27362288ad9ebcac`.
