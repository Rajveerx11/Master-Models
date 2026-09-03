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

- Frozen evaluation: 20 real tasks per specialist, 100 total.
- Every V2 set has exact 5 easy / 9 medium / 6 hard balance.
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
| frontend-stack | 20 frozen tasks | 242 retained V1 trajectories | Allowed after truthfulness re-audit | Re-audit |
| backend-stack | 20 frozen tasks | 276 source candidates | Open | Ready for generation |
| security-review | 20 frozen tasks | 62 source candidates | Open | Ready for generation |
| code-review | 20 frozen tasks | 332 source candidates | Open | Ready for generation |
| testing-qa | 20 frozen tasks | 84 source candidates | Open | Ready for generation |

## Current work queue

- [x] Define five-specialist V2 scope and 4B memory budget.
- [x] Add shared registry and dataset schemas.
- [x] Add deterministic source-inventory builder.
- [x] Generate source inventories: frontend 203, backend 276, security 62,
  code-review 332, testing/QA 84.
- [x] Build isolated eval review queues: 40 backend, 40 security, 40 code-review,
  and 32 testing/QA candidates.
- [x] Build the 121-record frontend score-7 semantic re-audit queue.
- [x] Human-review eval candidates through independent author/audit passes.
- [x] Freeze 20 real tasks each for backend, security, review, and QA.
- [x] Validate 100 tasks, immutable ancestry, difficulty balance, and hash isolation.
- [ ] Review non-eval source inventories for training-generation quality.
- [ ] Re-audit frontend score-7 records for unsupported claims.
- [ ] Build generation queues from non-eval commits.
- [ ] Generate, judge, deduplicate, and spot-check domain trajectories.
- [ ] Pin the exact Qwen3-4B tokenizer template.
- [ ] Build 3,072-token whole-record train/holdout splits.
- [ ] Build and run the self-contained Colab notebook.
- [ ] Run stock-versus-specialist frozen gates.

## Immediate next checkpoint

Re-audit the 121 frontend score-7 records and review non-eval source candidates.
Then generate a small 30-50 trajectory pilot per new domain, validate it, and inspect
quality before scaling toward each domain target.
