# First five frontend execution pilots

Executed 2026-09-07. **Five tasks checked; zero approved V2 gold records.**
All source changes live in isolated parent snapshots. Original source repositories,
V1 datasets and frozen evals are preserved. Nothing was trained, committed or pushed.

| Task | Observed parent failure | Final captured checks | Complete tokens |
|---|---|---|---:|
| 01: compact input | 36px input beside 32px control | 6 browser checks; TypeScript 5.7.3 | 4,378 |
| 10: keyless provider | Local selection/send blocked without API key | 3 unit tests; 4 browser checks; TypeScript 5.8.3 | 10,822 |
| 15: pane identity | Unknown/unchanged leaf updates cloned root | 3 unit tests; TypeScript 5.8.3 | 4,185 |
| 20: tooltip surface | Custom body retained default arrow color | 16 browser checks; TypeScript 5.8.3 | 8,064 |
| 29: pane cap | Ninth pane created at eight-pane limit | 1 hook test with boundary/control cases; TypeScript 5.8.3 | 6,989 |

The seven unit tests and 26 browser checks are focused fixture evidence. All five
source TypeScript checks returned zero. Screenshots for input focus, model selection
and all eight tooltip placement/variant combinations were inspected by the author.
This is not a full native-app, performance or live-model evaluation.

## Admission decision

**Do not expand this capture format to the remaining 25 tasks or train these rows.**
Every complete trace exceeds 3,072 tokens. All failed tool calls and full recorded
reads remain; nothing was truncated to make a row fit. The exported messages are a
mechanical projection of actual tool events, with no invented intermediate reasoning.
They are replay evidence, not approved V2 trajectory files.

The author previously inspected reference patches. That exposure is explicitly
recorded; no reference-unexposed or independent authoring is claimed. Independent
semantic review is still pending. No judge score or human approval was created.

Next: preflight the now-working harness outside new authoring episodes, capture
focused source ranges and concise actual check summaries with full raw artifacts,
then measure fresh complete episodes. Preserve these oversized traces. Obtain
independent semantic review before expanding to the remaining 25 tasks, assigning
train/holdout groups or building a training corpus.

## Evidence layout

- `manifest.json`: source-archive verification, edit-chain checks, artifact and
  harness hashes. All changed archived files were compared; only declared task
  paths and the documented task-01 setup overlay differ.
- Each `frontend-pilot-XX/`: exact setup/tool/command events, source provenance,
  reviewable patch, and browser results/screenshots where required.
- `review-decisions.json`: one-based event references distinguishing accepted
  baselines/final checks from harness failures, plus explicit review limitations.
- `records/`: every captured tool exchange projected into complete messages.
- `token-fit.json`: measured lengths and record/rendered hashes.
- `harness-history/initial/`: initial dependency lock retained across the browser
  tooling update. Early events predate per-event harness hashes; they are not
  retroactively assigned invented historical harness identities.

Raw logs retain original machine paths and timestamps. Runtime browser artifacts
remain under `outputs/frontend-pilot/`; copies here are hash-bound and reviewable.
Source repositories and dependency downloads are still required for execution replay.
The selection queue under `../pilot/` preserves its original selection-time status;
this bundle is the current execution ledger.

## Material findings and limitations

- Task 01's parent manifest declared husky absent from its lockfile. A hash-guarded,
  install-only overlay removes that Git-hook dependency. No source lockfile changed.
- Early failures included duplicate React, a mock-resolution mistake, missing
  Chromium/CommonJS handling and missing Tailwind source scanning. They are retained
  as harness troubleshooting, not counted as product defect baselines.
- The Python capture CLI initially returned zero despite nonzero child results.
  Raw command metadata was always accurate; the CLI now propagates the exit code.
  Browser result files also receive a separate fail-closed check.
- Early pnpm commands through Git Bash are excluded from accepted typecheck evidence.
  Final checks invoked each snapshot's TypeScript executable directly through Node.
- Task 10 uses a recording mock at the Chat SDK send boundary and explicit browser
  stubs for native-adjacent controls. No network transport or model output is claimed.
- Task 20 inherits the body surface through Radix's positioning wrapper and clips
  it to a native triangle. This changes the previous rotated-square arrow shape.
  Solid default/red surfaces and four placements pass; gradients, all themes,
  collision cases and other browsers are not covered.
- Git archive applies CRLF conversion here. Git blob hashes and exported byte hashes
  differ; both source identities are retained and the captured edit chain is checked
  against actual archive bytes.

## Tokenizer and reproduction

Qwen3-4B tokenizer/template revision:
`1cfa9a7208912126459214e8b04321603b3df60c`.
[`qwen3-4b.pin.json`](../../../../../training/templates/qwen3-4b.pin.json) records
file/template hashes and render settings (`enable_thinking=false`,
`add_generation_prompt=false`). Only tokenizer/config files were downloaded.
The quantized training-base revision and tokenizer parity remain pending.

The [harness runbook](../../../../../scripts/frontend_pilot/README.md) describes
fresh-snapshot replay and setup boundaries. Verify the exported bundle with:

```powershell
py -3 scripts/validate_frontend_execution.py
py -3 -m unittest scripts.test_frontend_execution scripts.test_frontend_hardening scripts.test_gate_proxy scripts.test_v2_source_inventory
py -3 scripts/validate_frontend_pilot.py
py -3 scripts/validate_eval_tasks.py --require-v2
py -3 scripts/validate_v2_dataset.py --specialist frontend-stack
```

Implementation references:
[Tailwind explicit sources](https://tailwindcss.com/docs/detecting-classes-in-source-files#explicitly-registering-sources),
[Qwen tokenizer at the pinned revision](https://huggingface.co/Qwen/Qwen3-4B/blob/1cfa9a7208912126459214e8b04321603b3df60c/tokenizer_config.json).

Verification on 2026-09-07: execution integrity passed; 29 regression/guard tests
passed; all 30 selection specifications and 100 frozen eval tasks validated;
frontend foundation passed with 143 sources and zero V2 trajectories. The original
hardening audit remains deterministic. Protected-path comparison and staged diff
were empty; HEAD remains `f16899d39ae4a92a388989cc4cb7865f80c74b33`.
`runtime.json` preserves the initial setup observation; the final harness dependency
versions are bound by `manifest.json` and the current harness lockfile.
