# Task 01 - Forced tool calls conflict with JSON response format

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `40af6c40dd2a0b67a92bddf02d3315829b2eaac5`
Start commit: `a04704f159975ec39fe5c170af51519092975e4e`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

Gemini's OpenAI-compatible endpoint rejects a request when a single forced function call is combined with JSON response formatting. Adjust request construction so that exact combination is avoided. Requests without a forced tool must remain JSON-constrained, including the retry path after tools are stripped and requests that expose multiple tools.

## Success criteria (checkable)

- [ ] A request with exactly one forced tool omits JSON response formatting
- [ ] Tool-free and multi-tool requests retain JSON response formatting
- [ ] The retry path restores JSON formatting after removing tools
- [ ] Existing tool schemas and forced-tool selection remain unchanged
- [ ] Focused provider tests pass

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib build_request_payload
```

## Scoring: pass / partial / fail notes

- **pass** - only the incompatible single-forced-tool combination changes and all request-shape tests pass.
- **partial** - Gemini succeeds but another request shape loses its JSON constraint.
- **fail** - the rejected combination remains, tool selection changes, or checks fail.

## Graders-only reference evidence

Run this focused discriminator from the source checkout:

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib build_request_payload_keeps_response_format_for_multi_tool 2>&1
$code = $LASTEXITCODE
$output | Write-Output
if ($code -ne 0 -or $output -notmatch '1 passed') { exit 1 }
$source = Get-Content apps/desktop/src-tauri/src/providers/llm/openai_compat.rs -Raw
if ($source -notmatch 'if req\.tools\.len\(\) != 1' -or $source -notmatch 'obj\.insert\(\s*"response_format"') { exit 1 }
```

The exact command produces `0 passed` at `a04704f159975ec39fe5c170af51519092975e4e` and `1 passed` at `40af6c40dd2a0b67a92bddf02d3315829b2eaac5`.

The reference changes only `openai_compat.rs`, conditionally adds `response_format`, restores it on the strip-tools retry, and tests the single-tool and multi-tool shapes. Inspect with `git diff a04704f159975ec39fe5c170af51519092975e4e 40af6c40dd2a0b67a92bddf02d3315829b2eaac5 -- apps/desktop/src-tauri/src/providers/llm/openai_compat.rs`.
