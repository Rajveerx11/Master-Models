# Task 04 - Terminal output is held during small bursts

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `e823c8579967ed710a0932441b9d40ed6e8f4d77`
Start commit: `978f83ab5f388d2d0a1c965e2966b608573890be`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

The PTY flusher intentionally holds small output bursts, adding visible latency to prompts and interactive echo. Make pending output flush on one short, constant cadence. Keep the existing bounded buffer, overflow handling, channel-close exit, and final EOF drain intact.

## Success criteria (checkable)

- [ ] Pending PTY bytes flush on each short interval instead of waiting for burst age or size thresholds
- [ ] Empty iterations continue until the reader reports completion
- [ ] Channel closure still stops the flusher cleanly
- [ ] Backpressure limits and final EOF draining remain unchanged
- [ ] Rust checking passes

## Verification commands

```powershell
cargo check --manifest-path src-tauri/Cargo.toml
```

## Scoring: pass / partial / fail notes

- **pass** - adaptive burst holding is removed with a focused change while safety and shutdown behavior remain intact.
- **partial** - latency improves but obsolete adaptive state remains or an edge condition changes.
- **fail** - small output is still held, bytes can strand, or checking fails.

## Graders-only reference evidence

Run this policy discriminator:

```powershell
$source = Get-Content src-tauri/src/modules/pty/session.rs -Raw
if (-not $source.Contains('const FLUSH_INTERVAL: Duration = Duration::from_millis(4);') -or $source.Contains('BURST_MAX_AGE') -or $source.Contains('BURST_THRESHOLD')) { exit 1 }
```

This fails at `978f83ab5f388d2d0a1c965e2966b608573890be`, which still declares both adaptive burst thresholds, and passes at `e823c8579967ed710a0932441b9d40ed6e8f4d77`.

The reference replaces the adaptive burst policy with a constant four-millisecond drain in the PTY flusher and leaves reader, overflow, and waiter behavior untouched. Inspect with `git diff 978f83ab5f388d2d0a1c965e2966b608573890be e823c8579967ed710a0932441b9d40ed6e8f4d77 -- src-tauri/src/modules/pty/session.rs`.
