# V2 datasets

The V2 corpus is a collection of small, difficult, source-grounded datasets for five
Qwen3-4B specialists. Quality and eval isolation matter more than row count.

## Specialists

| ID | Target work | Current reusable data |
|---|---|---|
| `frontend-stack` | React, TypeScript, CSS, UI state and accessibility | 237 replay candidates; 5 quarantined; no V2 gold |
| `backend-stack` | APIs, services, persistence, concurrency, providers | None yet |
| `security-review` | trust boundaries, injection, path/auth/secret safety | None yet |
| `code-review` | defect discovery, evidence, severity, precise fixes | None yet |
| `testing-qa` | test design, flaky tests, mutation, integration and CI | None yet |

Machine-readable status lives in `datasets/v2-registry.json`.

## Required order

```text
real Git history
  -> source candidate inventory
  -> frozen eval tasks and reserved commits
  -> training generation queue excluding all eval evidence
  -> source-grounded tool trajectories
  -> structural validation
  -> judge scoring + deterministic checks
  -> semantic spot-check
  -> deduplication and contamination scan
  -> train/holdout split
  -> whole-record token-bound derivative
```

For any domain whose eval state is not `frozen`, training generation is blocked.
All five domains are now frozen. A V2 eval-reference parser defect was repaired on
2026-09-06: frontend inventory now contains 143 candidates after excluding 60 reserved
reference/parent collisions. Other domains' historical inventories require rebuilding
with the corrected parser before generation. The [30 selected frontend pilot tasks](frontend-stack/v2/review/pilot/README.md)
have scoped acceptance checks. The [first five execution bundles](frontend-stack/v2/review/execution-pilot/README.md)
pass focused/browser/type checks, but all complete traces exceed 3,072 tokens and
independent review remains pending. No task specification, oversized evidence record
or old replay candidate is training data.

## V2 trajectory contract

One JSON object per line. The normative schema is
`datasets/schema/trajectory-v2.schema.json`.

Required fields:

- `id`: stable domain-prefixed identifier.
- `schema_version`: integer `2`.
- `specialist`: one registry specialist ID.
- `source`: repository, commit, parent, file paths, and license/provenance note.
- `messages`: complete user/assistant/tool trajectory.
- `tools`: the exact serving tool schemas for tool-bearing records.
- `quality`: difficulty, skills, verification commands, and review state.

The final assistant message may claim a check passed only when a preceding tool result
contains that successful check. Tool results must be contiguous with their calls.

## Size targets

These are quality targets, not quotas.

| Split component | Per specialist |
|---|---:|
| Gold domain trajectories | 180-300 |
| Loss holdout | 5%, minimum 12 |
| General/tool anti-forgetting | 60-100 shared records |
| Frozen repository eval | 20 tasks, never in train/holdout |

Prefer 2-8 meaningful tool calls, one real failure/recovery where natural, and at least
one actual verification step. Reject padded or theatrical tool use.

## Context policy

V2 targets 3,072 rendered tokens, with a 2,048 fallback for T4 instability. Filtering
keeps or drops an entire trajectory. It never truncates a message, call, result, or
assistant answer.

## V1 data

`datasets/frontend-stack/filtered/` and `datasets/frontend-stack/final/` are preserved
as V1 evidence. Do not overwrite them. V2 outputs use explicit `v2/` subdirectories.

The 2026-09-06 whole-corpus audit screened all 242 retained frontend records, including
scores 8 and 9. Five are quarantined and four explanations are corrected in a separate
237-record candidate set. Every candidate is explicitly training-ineligible: V1 tool
results were authored synthetically and lack captured execution and source identity.
See [the report](frontend-stack/v2/review/hardening/REPORT.md) for evidence and replay
requirements. High judge scores do not substitute for semantic or execution review.

## Commands

```powershell
py -3 scripts/build_v2_source_inventory.py
py -3 scripts/build_v2_queues.py
py -3 scripts/validate_eval_tasks.py --require-v2
py -3 scripts/validate_v2_dataset.py --registry datasets/v2-registry.json
```

The validator treats an absent not-yet-generated split as `pending`. It fails malformed
files, duplicate IDs/content, eval-commit overlap, invalid tool exchanges, or unsupported
verification claims.
