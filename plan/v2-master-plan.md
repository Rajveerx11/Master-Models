# Master Models V2 execution plan

**Status:** approved and active

**Target:** five Qwen3-4B specialists that fit free Google Colab

**Done:** reproducible datasets, trained GGUFs, and stock-versus-specialist gate results

## Outcome

Build specialists for frontend, backend, security review, code review, and testing/QA.
Each model receives a compact, difficult, source-grounded corpus and must beat stock
Qwen3-4B on a frozen domain gate. The project stops or repairs any domain that does not
show measurable improvement.

## Hard decisions

| Decision | Choice | Reason |
|---|---|---|
| Base size | Qwen3-4B | Practical download, QLoRA, merge, and export footprint on free Colab |
| Dataset size | 180-300 gold domain rows | Quality and reviewability over bulk |
| Default context | 3,072 whole-record tokens | Useful tool traces with T4 margin |
| Fallback context | 2,048 whole-record tokens | Recovery path for unstable runtimes |
| Evaluation | 20 frozen repository tasks/domain | Measures real work, not imitation |
| Release baseline | stock Qwen3-4B | Isolates the effect of fine-tuning |
| Orchestration | Deferred | Needs proven specialists and real routing logs |

## Data flow

```text
local Git repositories
├─ reserved branch: frozen eval commits -> 20 immutable tasks -> A/B gate
└─ training branch: non-eval commits -> generation queue -> tool trajectories
                                          ├─ structural validation
                                          ├─ judge + deterministic checks
                                          ├─ human semantic spot-check
                                          └─ dedupe/contamination scan
                                                   -> train/holdout
                                                   -> 3072-token derivative
                                                   -> Colab QLoRA
                                                   -> verified Q4_K_M GGUF
```

## Repository changes

| Area | Files | Purpose |
|---|---|---|
| Control plane | `datasets/v2-registry.json` | domains, sources, gates, budgets |
| Contracts | `datasets/schema/*.json` | source and trajectory validation |
| Acquisition | `scripts/build_v2_source_inventory.py` | deterministic Git candidate mining |
| Validation | `scripts/validate_v2_dataset.py` | schema, tools, duplicates, leakage, truth claims |
| Domain plans | `plan/specialists/*.md` | skill mix, exclusions, data and gate targets |
| Training | `training/README.md` | Colab-safe 4B recipe |

## Phase 1 — foundations

- [x] Select Qwen3-4B and define resource limits.
- [x] Define five specialist boundaries.
- [x] Add registry, schemas, inventory builder, and validator.
- [x] Generate source inventories from available local repositories.
- [x] Review eval candidate balance and remove weak/documentation-only commits.
- [x] Record immutable repository identity and license/provenance.
- [ ] Review non-eval source candidates before trajectory generation.
- [x] Select 30 scoped frontend pilot tasks; correct eval reservation parsing (143 frontend sources remain).

Exit: every specialist has a reviewed candidate pool with no known eval overlap.

## Phase 2 — freeze evaluation

- [x] Reuse the existing 20-task frontend set.
- [x] Freeze 20 backend tasks.
- [x] Freeze 20 security tasks.
- [x] Freeze 20 code-review tasks.
- [x] Freeze 20 testing/QA tasks.
- [x] Add all reference hashes to reservations before training generation.

Target balance per set: 5 easy, 9 medium, 6 hard. A task must have a reproducible parent
revision, focused prompt, objective checks, and graders-only reference evidence.

Exit: registry says `frozen`, task files validate, and generation refuses reserved
commits.

## Phase 3 — build datasets

Frontend:

- Whole-corpus static screening completed: 5 retained records quarantined, 4
  explanation repairs, 237 candidates awaiting real execution.
- Five of the [selected 30-task pilot](../datasets/frontend-stack/v2/review/pilot/README.md)
  tasks pass captured checks with a pinned harness. All five complete traces exceed
  3,072 tokens; repair capture length and obtain independent review before expansion.
  V1 examples remain coverage ideas; never invent provenance for them.
- Review semantics at every score, including 8/9; judge scores missed incorrect
  React, CSS, date and accessibility explanations.
- Capture real tool execution and verify both failure and corrected behavior before
  promoting any record. See `datasets/frontend-stack/v2/review/hardening/REPORT.md`.
- Add 30-50 gap-targeted examples only if the audited pool lacks important skills.

New domains:

- Build queues only from reviewed non-eval commits.
- Generate source-grounded prompts and complete pi-compatible trajectories.
- Require useful inspection, minimal changes, and real verification.
- Score tool correctness, logic, code/review quality, realism, and diversity.
- Keep only records scoring at least 8/10; manually inspect every borderline record.

All domains:

- Deduplicate normalized prompts and assistant outputs.
- Scan source hashes and text against eval material.
- Group by source task before splitting; variations of one commit stay together.
- Add 60-100 shared general/tool anti-forgetting records.
- Create deterministic train/holdout splits.
- Render with the pinned 4B template and filter whole records at 3,072 tokens.

Exit: manifest records inputs, counts, hashes, template hash, token distribution,
licenses, drops, and review decisions.

## Phase 4 — Colab training

- Pin exact packages, base revision, tokenizer, template, and tool schemas.
- Build a self-contained notebook from committed validated inputs.
- Guard free disk and free VRAM before loading.
- Probe the longest record for one optimizer step.
- Train two epochs with rank-16 QLoRA and checkpoint resume.
- Export one Q4_K_M file and record size, SHA-256, and GGUF header.

Train frontend first. Train another domain only after frontend completes the full gate;
this prevents multiplying a broken recipe.

## Phase 5 — qualification and gates

- Verify server prompt matches the training template.
- Pass the domain 10/10 smoke suite.
- Run trained arm A and stock-4B arm B on identical frozen tasks.
- Record pass/partial/fail, checks, tool validity, tool choice, errors, and patch.
- Ship only a clear win without material safety/tool regression.

## Phase 6 — portfolio decision

- Continue winning specialists.
- Repair one time when failure analysis points to a specific data gap.
- Stop a domain after a second non-win unless new evidence changes the hypothesis.
- Start orchestrator data collection only after at least three specialists win.

## Risks

| Risk | Control |
|---|---|
| Synthetic confidence without execution | Require matching tool-result evidence |
| Eval contamination | Reserve commits first; scan hashes and text |
| Small-model capacity overload | Narrow domain boundaries and 180-300 gold rows |
| Colab disk/OOM failure | 4B base, 3,072 cap, 2,048 fallback, 20-25 GB free |
| Template drift | Pin and hash tokenizer template; train/serve comparison |
| Dataset quantity bias | Use coverage matrix and stop at quality target |
| Overfitting | 5% holdout, two epochs, stock baseline, frozen repository gate |

## Verification

```powershell
py -3 scripts/build_v2_source_inventory.py --check
py -3 scripts/build_v2_queues.py --check
py -3 scripts/validate_eval_tasks.py --require-v2
py -3 scripts/validate_v2_dataset.py --registry datasets/v2-registry.json
py -3 scripts/build_train_mix.py --demo
py -3 -m unittest scripts.test_gate_proxy
```

Final proof is not these local checks. It is a committed per-domain A/B gate report.
