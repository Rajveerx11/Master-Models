# Task 11 - PTY output pays a base64 JSON tax

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `578f1d5c508c8d4ee4e1b702334d3512c45f4cb2`
Start commit: `f5b54a9a877bbb768c486a5c221223d949e8c4d1`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Terminal output is base64-encoded into tagged JSON events before crossing Tauri IPC, then decoded in JavaScript. Remove that avoidable CPU and allocation cost by carrying PTY data as raw bytes. Keep exit notifications typed and separate, preserve final buffered output before exit, and ensure a closed frontend channel ends the relevant worker safely.

## Success criteria (checkable)

- [ ] PTY data crosses IPC as raw bytes without base64 or JSON byte arrays
- [ ] Exit codes use a separate typed channel
- [ ] Pending tail bytes are delivered before the exit event
- [ ] Channel closure stops producer work safely
- [ ] Frontend receives an `ArrayBuffer` and forwards a `Uint8Array` to existing handlers
- [ ] The base64 dependency and decoder are removed
- [ ] TypeScript and Rust checks pass

## Verification commands

```powershell
pnpm exec tsc --noEmit
cargo check --manifest-path src-tauri/Cargo.toml
```

## Scoring: pass / partial / fail notes

- **pass** - raw-byte transport replaces base64 end-to-end without breaking data/exit ordering.
- **partial** - raw data works but cleanup, tail delivery, dependency removal, or typing is incomplete.
- **fail** - output is corrupted/lost, base64 remains in the path, or checks fail.

## Graders-only reference evidence

Run this end-to-end transport discriminator:

```powershell
$cargo = Get-Content src-tauri/Cargo.toml -Raw
$session = Get-Content src-tauri/src/modules/pty/session.rs -Raw
$bridge = Get-Content src/modules/terminal/lib/pty-bridge.ts -Raw
if ($cargo -match '(?m)^base64\s*=' -or $session.Contains('PtyEvent') -or -not $session.Contains('Channel<Response>') -or -not $session.Contains('Channel<i32>') -or -not $bridge.Contains('Channel<ArrayBuffer>') -or -not $bridge.Contains('new Uint8Array(buf)') -or $bridge.Contains('decodeBase64')) { exit 1 }
```

The command fails at `f5b54a9a877bbb768c486a5c221223d949e8c4d1` on the dependency, tagged event, and decoder checks; it passes at `578f1d5c508c8d4ee4e1b702334d3512c45f4cb2`.

The reference replaces the multiplexed serialized `PtyEvent` with `Channel<Response>` plus `Channel<i32>`, removes base64, sends the drained tail before exit, and adapts the TypeScript bridge to `ArrayBuffer`. Inspect with `git diff f5b54a9a877bbb768c486a5c221223d949e8c4d1 578f1d5c508c8d4ee4e1b702334d3512c45f4cb2 -- src-tauri/src/modules/pty src/modules/terminal/lib/pty-bridge.ts src-tauri/Cargo.toml`.
