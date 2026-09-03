# Master Models V2

Master Models builds small coding specialists that can be fine-tuned on free Google
Colab hardware and measured on real repository tasks.

## V2 decision

- Base model: **Qwen3-4B**, loaded in 4-bit for QLoRA.
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
| Frontend frozen eval | Ready: 20 tasks |
| Frontend reusable corpus | Ready for V2 re-audit: 242 domain trajectories |
| All specialist source inventories | Ready and eval-isolated |
| All specialist frozen evals | Ready: 20 tasks each, 100 total |
| Qwen3-4B template, bounded splits, notebook | Pending |
| V2 training and gates | Pending |

See [STATUS.md](STATUS.md) for the live checkpoint and
[plan/v2-master-plan.md](plan/v2-master-plan.md) for the execution order.

## Repository map

```text
datasets/    V1 corpus, V2 contracts, source inventories, queues, train/holdout sets
evals/       Frozen real-repository tasks and results
plan/        V2 master plan, specialist plans, and archived V1 research
plans/       Agent-native copy of the V2 execution plan
prompts/     Generation and judging provenance
scripts/     Inventory, validation, mixing, training, serving, and gate tools
training/    Colab-safe recipes, tool schemas, and pinned chat templates
```

## Non-negotiable rules

1. Do not train on this machine. A prior local QLoRA run caused an NVIDIA driver
   bugcheck. Use Colab; use local GPU only for inference and evaluation.
2. Freeze a specialist's eval set before generating its train trajectories.
3. Never put eval prompts, commits, patches, or paraphrases into training data.
4. Keep whole trajectories. Do not truncate messages or tool exchanges.
5. Train and serve with the same pinned tokenizer chat template and tool schemas.
6. A specialist ships only after it beats stock Qwen3-4B on its frozen gate.

## First commands

```powershell
py -3 scripts/build_v2_source_inventory.py
py -3 scripts/build_v2_queues.py
py -3 scripts/validate_eval_tasks.py --require-v2
py -3 scripts/validate_v2_dataset.py --registry datasets/v2-registry.json
py -3 scripts/build_train_mix.py --demo
py -3 -m unittest scripts.test_gate_proxy
```

V2 source inventory output is deterministic. It excludes every commit referenced by
the committed eval suite and writes only commit metadata; raw repository contents and
model weights remain local.
