# Archived V1 release plan — frontend-stack Qwen3-8B

> Historical record. V2 uses Qwen3-4B and is defined in
> `plan/v2-master-plan.md`. Do not use this file as the active runbook.

**Last revised:** 2026-08-06

**Scope:** one Qwen3-8B frontend-stack specialist, exported as Q4_K_M and evaluated
against two stock controls.

## Release objective

Determine whether frontend specialization improves Qwen3-8B and whether that improved
8B is competitive with stock Qwen3-Coder-30B-A3B on 20 frozen real-repository tasks.

V1 finishes when verified results exist, not only when weights exist. A loss still
finishes the experiment if evidence is complete and honestly recorded.

## Current checkpoint

| Workstream | State |
|---|---|
| Frontend eval freeze | Complete: 20 tasks, commit `f2fb8f1` |
| Dataset generation and judging | Complete: 350 raw, 245 score-qualified |
| Adversarial spot-check | Complete: 242 retained domain trajectories |
| Final source mix | Complete: 404 records, 384 train / 20 holdout |
| 4,096-token bounded split | Complete: 328 train / 18 holdout |
| Colab notebook | Complete, self-contained, repository/Drive hashes match |
| Training | Reported complete in Colab handoff; local proof not yet downloaded |
| Specialist GGUF | Not confirmed locally or in expected Drive artifact folder |
| Template and smoke qualification | Pending |
| Gate A/B/C | Pending |

Live resume evidence: `STATUS.md`. Operational commands: `training/README.md`.

## Scope decisions

- Frontend-stack only. Backend-stack and code-review remain deferred.
- No local training after RTX 4060 `nvlddmkm.sys` bugcheck.
- Whole-record 4,096-token training set; no trajectory truncation.
- One specialist handles one whole task; no mid-task model interleaving.
- Arm B, stock Qwen3-8B, is mandatory to isolate training effect.
- All models use Q4_K_M for a fair quantization comparison.
- Every outcome is committed. A losing gate is useful evidence, not hidden failure.

## Phase 1 — acquire verified specialist artifact

1. Inspect active Colab final export cell.
2. Re-run only that cell if `artifact.json` and download completion are absent.
3. Confirm final filename, size, `GGUF` header, SHA-256, and Q4_K_M metadata.
4. Download `frontend-stack-qwen3-8b-q4_k_m.gguf` fully.
5. Compare local byte count and SHA-256 with Colab metadata.

Exit criterion: one locally readable specialist GGUF with matching artifact metadata.

## Phase 2 — qualify served candidate

1. Start llama-server with specialist GGUF and `--jinja` on port 18081.
2. Run `scripts/verify_server_template.py` directly against llama-server.
3. Require `json_whitespace_normalized_match: true`.
4. Run six guard-proxy unit tests.
5. Start guard proxy on port 18080.
6. Run `scripts/smoke_model.py` through proxy.
7. Require 10/10.

Broken tool JSON, template mismatch, or smoke failure blocks the gate. Fix serving
contract before changing dataset or comparing capability.

## Phase 3 — prepare controls

Required artifacts:

- Arm A: trained frontend-stack Qwen3-8B Q4_K_M
- Arm B: stock Qwen3-8B Q4_K_M from same base family
- Arm C: stock Qwen3-Coder-30B-A3B Q4_K_M

Record path, byte count, SHA-256, llama-server version, Neura commit/config, and model
metadata for each arm. Keep guard behavior identical.

Exit criterion: all three artifacts resolve locally and each arm can serve through the
same proxy/harness configuration.

## Phase 4 — run frozen gate

Run all 20 tasks for A, B, and C: 60 total runs.

For each arm:

1. Launch exact model on 18081 with `--jinja`.
2. Launch fresh arm-specific proxy log on 18080.
3. Run `scripts/run_gate.py --arm <A|B|C> --tasks all` with exact model path.
4. Inspect failures and resume only matching manifests.
5. Grade against each frozen task's success criteria.

Use same day, harness, Neura configuration, prompts, timeouts, dependency policy, and
scoring standard where practical. Record every unavoidable deviation.

## Decision rule

Read A versus B first; that is training verdict. Read A versus C second; that is size
and deployment verdict.

| Outcome | Verdict | Action |
|---|---|---|
| A > B and A ≥ C | Training works; 8B size sufficient | Bank recipe; v1 wins; consider domain 2 |
| A > B and A < C | Training works; 8B remains weaker than 30B | Bank recipe; decide larger base versus stock 30B |
| A ≈ B | Training had no material effect | Stop adding data; diagnose masking, learning rate, epochs, and mix |
| A < B | Training hurt base | Stop; inspect template, response masking, schema conversion, then data |

Hard invalidation: A's tool-call validity materially below B. Treat as train/serve
mismatch, repair it, and rerun before reading capability scores.

## Definition of done

- [x] Frontend eval frozen and committed.
- [x] 242 spot-checked domain trajectories mixed with licensed anti-forgetting data.
- [x] Deterministic 384/20 source split and 328/18 bounded split committed.
- [x] Final standalone Colab workflow committed and mirrored.
- [ ] Specialist Q4_K_M GGUF downloaded and hash-verified.
- [ ] Server-template normalized match passes.
- [ ] Local post-export smoke test passes 10/10.
- [ ] Stock Qwen3-8B Q4_K_M control available.
- [ ] Stock Qwen3-Coder-30B-A3B Q4_K_M control available.
- [ ] Arms A, B, and C complete and graded.
- [ ] Consolidated result committed under `evals/results/`.

## Preserved historical deviations

- Original plan targeted three domains and thousands of trajectories. Throughput and
  quality evidence reduced v1 to one domain and 350 generated trajectories.
- Seed-first design was not followed beyond early pilots; later batches generated from
  explicit contracts and calibrated judge anchors.
- Batches 1 and 2 preceded eval freeze. Tasks were mined later from private repository
  history, preventing leakage, but ordering deviation remains real.
- Original two-arm gate omitted stock Qwen3-8B. Arm B was added because A versus C
  alone confounds training effect with model size.

Research timeline, teacher calibration, batch lessons, and schema investigations remain
in `plan/dataset-generation-research.md`, `prompts/`, and
`datasets/frontend-stack/final/MANIFEST.md`.
