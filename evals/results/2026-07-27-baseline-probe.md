# Baseline probe — stock Qwen3-Coder-30B-A3B (Q4_K_M, llama.cpp, jinja tools)

**Informal edge-case probe, NOT the frozen gate.** 16 auto-scored probes,
temp 0.1, `scripts/probe_baseline.py`, raw in `2026-07-27-baseline-probe.jsonl`.
Server: llama.cpp on :8081 (8080 squatted by Apache — see fixes), ~12 tok/s.

## Score: 9/16

| Category | Pass | Fail |
|---|---|---|
| Tool mechanics (9) | 6 | simple_tool_call, nested_json_args, empty_file_result |
| Code vs conventions (5) | 1 | controlled_input, async_submit_guard, ts_strict_catch, anti_slop_fake_data |
| Format discipline (2) | 2 | — |

## What it's good at (don't over-invest dataset here)
- No invented tools under pressure; sane ENOENT recovery (grep'd for the file).
- Multi-turn continuation (read → correct edit_file), needle-edit in 120-line file.
- User-over-system instruction conflict; bare-JSON output; admits it can't know
  unseen file contents (no fabrication). Icon-button a11y (aria-label) fine.

## Failure map

1. **Tool-call serialization flakiness (2/9 tool probes).** Model emitted Qwen XML
   (`<function=read_file><parameter=path>...`) as raw text with a stray
   `</tool_call>` closer — llama.cpp's parser produced NO structured tool_calls.
   Same server parsed other probes fine → format is intermittently malformed
   (missing `<tool_call>` opener). The harness dies exactly here.
2. **Empty tool result stalls the loop.** Given `read_file` → `""`, it said
   "let me check the content" and called nothing. Agent loop deadlock.
3. **Pre-hooks-era React under default prompting.** `React.FC` (twice),
   imperative DOM (`querySelector` + `.disabled = true`) instead of state,
   `(error as any)` despite "no any" instruction, `example.com` emails +
   placeholder-as-example. Functional logic mostly right (finally-reset was
   present) — style/conventions wrong.

## Fixes

- **Harness (pi/Hermes):** (a) parse-retry guard — if reply text matches
  `<function=` but no structured tool_calls, re-prompt once "re-emit as a valid
  tool call"; (b) normalize empty tool results to `"(file is empty — 0 bytes)"`
  so the model acts instead of stalling; (c) generous timeouts (~12 tok/s local).
- **Dataset (batch 2+):** add topic cells for the observed failures — empty-file
  handling, edits with escaped quotes/newlines, isSubmitting-state submit guards,
  `catch (e: unknown)` narrowing; conventions file already bans React.FC/DOM
  poking/fake emails — judge enforces.
- **launch.ps1:** port-listen check is a false positive when Apache holds 8080 —
  probe `GET /health` instead of `Get-NetTCPConnection`, and fall back to 8081.
- **Specialist bet reading:** baseline is strong on agent logic, weak on tool
  serialization + modern conventions — both highly trainable. The gate is
  winnable exactly where the dataset already aims.

## v2 — harness guards + conventions injection (same day)
`--guards --conventions` → **11/16** (`...probe-v2.jsonl`):
- **Tool mechanics 9/9** (was 6/9). Guard A (deterministic XML repair + one
  re-prompt) fixed both serialization fails; Guard B ("(file is empty — 0 bytes)")
  fixed the empty-result deadlock. Harness guards fully solve the tool failures.
- **Code conventions 0/5** (was 1/5) with the 97-line conventions file in the
  system prompt. Structure improved (named exports, focus-visible, dropped
  `as any`) but core habits survived explicit bans: `React.FC`, `example.com`
  data, `querySelector` DOM poking; one output dropped `aria-label`.

## v3 — code probes, 1100-token budget (truncation ruled out)
Still **0/5** (`...probe-v3-code.jsonl`). Same habits, not a token-budget artifact.

## Conclusion
Tool reliability: solved in the harness, no training needed. Modern-React
conventions: **in-context prompting does not produce compliance at stock 30B** —
the rules must be trained into weights. This is the specialist's exact lane, and
the gate is winnable there. Guards (repair/retry + result normalization) are
mandatory harness features regardless of which model serves.
