# Master Models V2 status

**Checked:** 2026-09-03

**Branch:** `master`

**Base target:** `Qwen/Qwen3-4B` / `unsloth/Qwen3-4B-bnb-4bit`

## Honest status

V2 is in dataset foundation, not model training. The project should continue, but the
8B path should not. Qwen3-4B is the practical free-Colab target.

Local disk is sufficient: roughly 155 GB free on `C:` and 147 GB reported on `G:` at
the audit. Colab remains the tight resource, so each run must reserve 20-25 GB of
runtime storage for packages, checkpoints, merge, and GGUF export.

## Completed evidence

- V1 frontend eval: 20 frozen real tasks.
- V1 frontend raw generation: 350 judged trajectories.
- V1 retained frontend set: 242 trajectories after automatic filtering and spot-check.
- V1 final mix: 384 train / 20 holdout.
- V1 4,096-token derivative: 328 train / 18 holdout.
- Existing manifests and committed hashes verify.
- Dataset validator, mix demo, and six guard-proxy tests pass.
- Local source repositories needed for mining are available.

No verified trained GGUF or completed three-arm gate exists. V1 therefore produced
useful data and tooling, not a proven specialist.

## V2 specialist ledger

| Specialist | Eval | Source data | Train generation | State |
|---|---|---|---|---|
| frontend-stack | 20 frozen tasks | 242 retained V1 trajectories | Allowed after truthfulness re-audit | Active |
| backend-stack | Not frozen | Local Git history | Blocked by eval-first rule | Inventory |
| security-review | Not frozen | Local Git history | Blocked by eval-first rule | Inventory |
| code-review | Not frozen | Local Git history | Blocked by eval-first rule | Inventory |
| testing-qa | Not frozen | Local Git history | Blocked by eval-first rule | Inventory |

## Current work queue

- [x] Define five-specialist V2 scope and 4B memory budget.
- [x] Add shared registry and dataset schemas.
- [x] Add deterministic source-inventory builder.
- [x] Generate source inventories: frontend 203, backend 276, security 62,
  code-review 332, testing/QA 84.
- [x] Build isolated eval review queues: 40 backend, 40 security, 40 code-review,
  and 32 testing/QA candidates.
- [x] Build the 121-record frontend score-7 semantic re-audit queue.
- [ ] Human-review source inventories and eval candidates.
- [ ] Freeze 20 real tasks each for backend, security, review, and QA.
- [ ] Re-audit frontend score-7 records for unsupported claims.
- [ ] Build generation queues from non-eval commits.
- [ ] Generate, judge, deduplicate, and spot-check domain trajectories.
- [ ] Pin the exact Qwen3-4B tokenizer template.
- [ ] Build 3,072-token whole-record train/holdout splits.
- [ ] Build and run the self-contained Colab notebook.
- [ ] Run stock-versus-specialist frozen gates.

## Immediate next checkpoint

Commit reviewed source inventories and frozen eval tasks for the four new domains.
Only then open their training-generation queues. Frontend can proceed in parallel with
its V1 truthfulness re-audit because its eval set is already frozen.
