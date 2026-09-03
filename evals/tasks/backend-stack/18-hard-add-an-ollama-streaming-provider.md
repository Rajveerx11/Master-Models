# Task 18 - Add an Ollama streaming provider

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `b99ba97c03c4aef7c2b2254faa25fbf060a61e47`
Start commit: `c4b6c888056035a2fcc96c70563b8f9042072b18`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Implement the first concrete `LlmProvider` for a local Ollama server using its OpenAI-compatible streaming chat endpoint. Keep services on the repository's typed provider abstraction. Translate messages and tools into a lean request, parse SSE safely across arbitrary byte boundaries and line endings, emit typed text/tool/done chunks, map finish reasons and HTTP failures, and support an injectable base URL for deterministic tests. Ollama requires no authorization header.

## Success criteria (checkable)

- [ ] Requests target the configured Ollama chat-completions endpoint without auth
- [ ] Empty optional request fields are omitted and typed message/tool content translates correctly
- [ ] SSE framing works with LF, CRLF, fragmented chunks, and the terminal sentinel
- [ ] Text, incremental tool calls, finish reasons, and completion usage map to internal chunk types
- [ ] Invalid JSON and 4xx/5xx responses produce the appropriate typed errors
- [ ] The existing default `generate` operation can drain the stream into a response
- [ ] Pure and mocked HTTP tests plus strict Clippy pass

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib ollama
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - request, streaming, tool, completion, and error translation are complete and tested.
- **partial** - text streaming works but framing, tools, usage, errors, or base-URL testing is incomplete.
- **fail** - the provider violates the abstraction, corrupts streams, sends auth, or checks fail.

## Graders-only reference evidence

Run the exact module-scoped test discriminator:

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib providers::llm::ollama::tests 2>&1
$code = $LASTEXITCODE
$output | Write-Output
if ($code -ne 0 -or $output -notmatch '17 passed') { exit 1 }
```

The filter yields `0 passed` at `c4b6c888056035a2fcc96c70563b8f9042072b18` because the provider module is absent, and `17 passed` at `b99ba97c03c4aef7c2b2254faa25fbf060a61e47`.

The reference adds `providers/llm/ollama.rs`, registers it, adds streaming/mock dependencies, and supplies 17 pure and mocked tests for request building, SSE parsing, HTTP mapping, and stream draining. Inspect with `git diff c4b6c888056035a2fcc96c70563b8f9042072b18 b99ba97c03c4aef7c2b2254faa25fbf060a61e47 -- apps/desktop/src-tauri/Cargo.toml apps/desktop/src-tauri/src/providers/llm`.
