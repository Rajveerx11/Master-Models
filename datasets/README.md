# V2 datasets

The V2 corpus is a collection of small, difficult, source-grounded datasets for five
Qwen3-4B specialists. Quality and eval isolation matter more than row count.

## Specialists

| ID | Target work | Current reusable data |
|---|---|---|
| `frontend-stack` | React, TypeScript, CSS, UI state and accessibility | 242 V1 trajectories pending re-audit |
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
All five domains are now frozen. New-domain generation may use only commits retained
in the rebuilt source inventories; frontend still requires its V1 truthfulness re-audit.

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

The old 242-record frontend keep set remains valuable because its tool traces validate
and its tasks match the domain. It is not accepted unchanged: all score-7 examples and
any record with unsupported red/green or test claims require semantic review.

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
