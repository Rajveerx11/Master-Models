# Task 10 - Webview cannot call local model servers

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `24c67af1f6b3fb18fbc667da9f9e5529691440e3`
Start commit: `bca34e4c1b78ff28f66bc57f57e2f972dbca9a67`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Production webviews cannot reliably call LAN-hosted model servers because of browser CORS, mixed-content, and private-network restrictions. Add backend commands for ordinary and streaming AI HTTP requests. Preserve arbitrary methods, headers, request bytes, response status/headers/body, stream chunks as bytes, and stop work cleanly when the frontend drops its channel. Slow generations must not have a total deadline, but unreachable hosts need a connect timeout.

## Success criteria (checkable)

- [ ] Both buffered-response and streaming commands are registered with Tauri
- [ ] Methods, valid headers, and optional body bytes are forwarded
- [ ] Buffered responses return status, normalized headers, and raw body bytes
- [ ] Streaming reports headers, byte chunks, terminal completion, and errors as typed events
- [ ] A dropped channel stops streaming without continuing background work
- [ ] The client has a connect timeout but no total generation timeout
- [ ] Rust formatting and checking pass

## Verification commands

```powershell
cargo fmt --manifest-path src-tauri/Cargo.toml --check
cargo check --manifest-path src-tauri/Cargo.toml
```

## Scoring: pass / partial / fail notes

- **pass** - both proxy modes preserve the HTTP contract and stream lifecycle safely.
- **partial** - basic proxying works but streaming, cancellation, timeout, or response metadata is incomplete.
- **fail** - LAN requests still depend on the webview, data is corrupted, or checks fail.

## Graders-only reference evidence

Run this registered-command discriminator:

```powershell
$net = Get-Content src-tauri/src/modules/net.rs -Raw
$lib = Get-Content src-tauri/src/lib.rs -Raw
foreach ($marker in @('pub async fn ai_http_request', 'pub async fn ai_http_stream', 'connect_timeout(Duration::from_secs(10))', 'AiStreamEvent::Headers', 'AiStreamEvent::Chunk', 'AiStreamEvent::End')) { if (-not $net.Contains($marker)) { exit 1 } }
if (-not $lib.Contains('net::ai_http_request') -or -not $lib.Contains('net::ai_http_stream')) { exit 1 }
```

Both command declarations and registrations are absent at `bca34e4c1b78ff28f66bc57f57e2f972dbca9a67`; all required lifecycle markers pass at `24c67af1f6b3fb18fbc667da9f9e5529691440e3`.

The reference extends `modules/net.rs` with a shared request builder, header conversion, buffered response, tagged stream events, and Tauri channel streaming; it registers both commands and enables Reqwest streaming/Rustls. Inspect with `git diff bca34e4c1b78ff28f66bc57f57e2f972dbca9a67 24c67af1f6b3fb18fbc667da9f9e5529691440e3 -- src-tauri/Cargo.toml src-tauri/src/lib.rs src-tauri/src/modules/net.rs`.
