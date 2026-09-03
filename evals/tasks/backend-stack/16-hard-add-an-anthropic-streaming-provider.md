# Task 16 - Add an Anthropic streaming provider

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `05343dbab867ce50a9acdf66e8fccabf29f583fa`
Start commit: `e4a51ac06a565676ca124878d04b5b9a6dbd486c`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Implement an Anthropic backend provider behind the existing `LlmProvider` abstraction. Translate the repository's typed messages, tools, streaming chunks, usage, and finish reasons to and from Anthropic's Messages API without leaking its wire format into services. Support system prompts, tool use/results, incremental tool JSON, named SSE events, required authentication/version headers, default output limits, consistent HTTP error mapping, and custom base URLs for tests.

## Success criteria (checkable)

- [ ] Construction rejects empty/invalid keys and uses the required Anthropic headers
- [ ] Requests place system content at top level and translate text, tool use, and tool results correctly
- [ ] Required output token limits have a sensible default while caller overrides remain honored
- [ ] Streaming handles fragmented SSE text, tool inputs, usage accumulation, pings, stop reasons, and terminal completion
- [ ] HTTP auth, rate-limit, and provider failures map consistently with existing providers
- [ ] The implementation advertises correct tool, streaming, context, and output capabilities
- [ ] Pure and mocked end-to-end provider tests plus strict Clippy pass

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib anthropic
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - request translation and cross-event stream state are complete, tested, and abstraction-safe.
- **partial** - basic text streaming works but tools, usage, finish reasons, headers, or errors are incomplete.
- **fail** - wire translation is invalid, provider details leak into services, or checks fail.

## Graders-only reference evidence

Run the exact module-scoped test discriminator:

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib providers::llm::anthropic::tests 2>&1
$code = $LASTEXITCODE
$output | Write-Output
if ($code -ne 0 -or $output -notmatch '15 passed') { exit 1 }
```

The filter yields `0 passed` at `e4a51ac06a565676ca124878d04b5b9a6dbd486c` because the module is absent, and `15 passed` at `05343dbab867ce50a9acdf66e8fccabf29f583fa`.

The reference adds `providers/llm/anthropic.rs`, registers it in the provider module, and includes 15 pure/mockito tests covering request shape, content blocks, headers, SSE sequencing, errors, usage, and stop reasons. Inspect with `git diff e4a51ac06a565676ca124878d04b5b9a6dbd486c 05343dbab867ce50a9acdf66e8fccabf29f583fa -- apps/desktop/src-tauri/src/providers/llm`.
