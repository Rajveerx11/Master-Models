# Master Models V2

Master Models aims to build small coding specialists for free Google Colab
fine-tuning, measured on real repository tasks. The public V2 tooling is available;
training remains **BLOCKED**, and 4B Colab runtime compatibility is unverified.

## V2 decision

- Base model target: **Qwen3-4B**, 4-bit QLoRA.
- Specialists: frontend, backend, security review, code review, and testing/QA.
- Data strategy: fewer, harder, source-grounded trajectories.
- Evaluation: freeze real tasks before generating domain training data.
- Orchestrator: deferred until at least three specialists beat their stock 4B base.

The old Qwen3-8B frontend experiment is preserved as V1 evidence. It is not the
active training target because its Colab download, training, and export footprint is
too fragile for the free tier.

## Current state

| Area | State |
|---|---|
| V2 architecture and per-specialist plans | Ready |
| Shared V2 dataset schema and registry | Ready |
| All specialist frozen evals | Registry declares 20 tasks each, 100 total |
| Frontend final V2 corpus and splits | Missing required inputs; no complete approved final corpus published |
| V2 source inventory tooling | Candidate metadata only; Git lookups disable lazy fetching |
| Qwen3-4B base pin | Tokenizer/backend parity metadata only; no weights downloaded or training eligibility |
| Qwen3-4B Colab notebook | Published BLOCKED scaffold; empty payload, no executed cells or outputs |
| V2 training and release gates | BLOCKED; Colab runtime/probe and specialist qualification remain unverified |

See [STATUS.md](STATUS.md) for the existing project checkpoint and
[plan/v2-master-plan.md](plan/v2-master-plan.md) for the execution order.
The V1 mix and archived 8B notebook are historical evidence, not approved V2
training inputs.

### Public training tooling

- [Training contract](scripts/v2_training_contract.py): stdlib-only, model-free,
  fail-closed checks for hash-bound inputs, independent review and grouped splits.
  Passing this data contract does not authorize training.
- [Colab builder](scripts/build_v2_colab.py): deterministic generator for the
  [4B notebook](notebooks/frontend_stack_qwen3_4b_colab.ipynb). The published
  scaffold stops before package installation, ML imports or weight downloads.
- [Regression tests](scripts/test_v2_training.py): synthetic fixtures and mocks,
  not real corpus admission, optimizer proof or model benchmarks.
- [Colab requirements](training/requirements-v2-colab.txt): provisional direct
  pins, **not a verified compatibility lock**. The
  [base pin](training/templates/qwen3-4b.base-pin.json) records tokenizer/backend
  parity only (`weights_downloaded: false`, `training_eligible: false`).

## Repository map

```text
datasets/    V1 corpus, V2 contracts, source inventories, queues, train/holdout sets
evals/       Frozen real-repository tasks and results
notebooks/   BLOCKED V2 4B scaffold and archived V1 notebook
plan/        V2 master plan, specialist plans, and archived V1 research
plans/       Agent-native copy of the V2 execution plan
prompts/     Generation and judging provenance
scripts/     Inventory, validation, mixing, training, serving, and gate tools
training/    Provisional Colab recipe, tool schemas, and pinned chat templates
```

## Non-negotiable rules

1. Do not train on this machine. A prior local QLoRA run caused an NVIDIA driver
   bugcheck. Use Colab; use local GPU only for inference and evaluation.
2. Freeze a specialist's eval set before generating its train trajectories.
3. Never put eval prompts, commits, patches, or paraphrases into training data.
   Gold authors must work blind-first, isolated from reference answers/patches;
   reference-exposed replays are not gold.
4. Require at least 180 approved gold records and 60 distinct, separately reviewed
   general records. Keep whole trajectories within 3,072 tokens under the actual
   pinned native rendering; never truncate messages or tool exchanges.
5. Require two current-hash, substantive independent semantic and provenance
   reviews, the declared spot-check policy, and source-family-grouped holdout isolation.
   File hashes and synthetic tests cannot establish semantic approval.
6. Train and serve with the same pinned tokenizer chat template and tool schemas.
   Data admission, verified Colab compatibility, a genuine isolated optimizer
   probe and explicit training authorization are separate gates.
7. A specialist ships only after genuine baselines/controls and stock Qwen3-4B
   comparison on its frozen gate; export alone is not release approval.

## Safe local quickstart

From the repository root, these checks use the Python standard library; no ML
packages, model downloads or GPU are needed:

```powershell
py -3 -B -m unittest scripts.test_v2_source_inventory scripts.test_v2_training -v
py -3 -B scripts/v2_training_contract.py
py -3 -B scripts/build_v2_colab.py --check
```

The published contract reports **BLOCKED** and exits with code 2 because final V2
inputs are missing. The builder's `--check` only verifies scaffold synchronization;
it is **not readiness or training permission**. Do not select a Colab GPU or run the
notebook as a training job while blocked. No trained V2 weights are delivered.

V2 source inventory output is deterministic candidate metadata, not training data.
It reserves frozen-eval reference commits and their parents; Git lookups set
`GIT_NO_LAZY_FETCH=1` to avoid fetching missing objects from partial clones.
Raw source checkouts and model weights remain local.
