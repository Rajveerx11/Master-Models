# Master Models V2 status

**Checked:** 2026-09-07

**Branch:** `master`

**Base target:** `Qwen/Qwen3-4B` / `unsloth/Qwen3-4B-bnb-4bit`

## Honest status

Frontend hardening audit is complete at the static-screening stage. All 350 raw
trajectories, 242 retained records, seeds, and final mixtures were screened. Five
retained examples are quarantined; four explanations were corrected in separate
candidate copies; three malformed general/tool examples are excluded. The 237
remaining frontend candidates still require source-grounded rebuilding and captured
execution. **Zero V2 gold records are approved. Do not train the old V1 mix.**

See [the hardening report](datasets/frontend-stack/v2/review/hardening/REPORT.md).
This does not claim independent semantic approval or execution of every record.

The [30-task pilot source queue](datasets/frontend-stack/v2/review/pilot/README.md)
is selected: 22 terax-ai tasks and eight testing-ide tasks, with scoped acceptance
checks and real Git/dependency hashes. Five tasks now have captured failing
baselines, scoped patches, seven passing unit tests, 26 passing browser checks and
five passing source TypeScript checks. Their complete traces all exceed 3,072 tokens
(4,185–10,822). Independent review remains pending; gold stays zero. See the
[execution report](datasets/frontend-stack/v2/review/execution-pilot/README.md).
A newly
found inventory parser bug omitted V2 eval references; fixing it excluded 60
frontend candidates and reduced the source inventory from 203 to 143. Other
specialists' historical inventories require refresh before generation.

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
- Frontend foundation, pilot metadata and execution-evidence validators pass;
  29 regression/guard tests pass. All 100 frozen eval tasks revalidated on 2026-09-07.
- Full-registry validation rejects the historical backend inventory's eval overlap;
  other-domain inventories must be refreshed before use. Earlier mix-demo evidence is unchanged.
- Local source repositories needed for mining are available.

No verified trained GGUF or completed three-arm gate exists. V1 therefore produced
useful data and tooling, not a proven specialist.

## V2 specialist ledger

| Specialist | Eval | Source data | Train generation | State |
|---|---|---|---|---|
| frontend-stack | 20 frozen tasks | 143 source candidates; 30 pilot tasks selected | Fix capture length; independent review before expansion | 5 executed / 0 gold |
| backend-stack | 20 frozen tasks | 276 historical source candidates | Wait | Eval isolation refresh required |
| security-review | 20 frozen tasks | 62 historical source candidates | Wait | Eval isolation refresh required |
| code-review | 20 frozen tasks | 332 historical source candidates | Wait | Eval isolation refresh required |
| testing-qa | 20 frozen tasks | 84 historical source candidates | Wait | Eval isolation refresh required |

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
- [x] Repair V2 eval reference parsing; refresh frontend inventory to 143 candidates.
- [x] Select 30 frontend pilot tasks with scoped checks and pending-only status.
- [x] Screen all frontend V1 records; quarantine confirmed defects and repair four explanations.
- [ ] Rebuild frontend candidates with real source identity and captured execution; independently review semantics.
- [ ] Build generation queues from non-eval commits.
- [ ] Generate, judge, deduplicate, and spot-check domain trajectories.
- [x] Pin Qwen3-4B tokenizer/template and measure the five complete pilot traces.
- [ ] Verify quantized training-base revision and tokenizer/template parity.
- [ ] Build 3,072-token whole-record train/holdout splits.
- [ ] Build and run the self-contained Colab notebook.
- [ ] Run stock-versus-specialist frozen gates.

## Immediate next checkpoint

Review the five execution bundles independently and fix capture length before
expanding to the remaining 25 tasks. Preflight the harness outside new authoring
episodes, then capture focused source reads and concise real check summaries while
retaining complete raw logs. Measure fresh complete episodes; never truncate or
rewrite these oversized records. The old 237 candidates remain coverage ideas.
Training and other-domain expansion remain blocked.
