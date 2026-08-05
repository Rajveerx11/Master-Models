# Master Models

Master Models tests one concrete bet: can a carefully trained small specialist beat
its stock base and remain competitive with a much larger general coding model on real
repository work?

The first specialist targets frontend-stack work: React, TypeScript, CSS, component
design conventions, and pi-compatible tool use. Training uses Qwen3-8B QLoRA. Serving
uses llama.cpp. Release requires a frozen, three-arm gate—not subjective output review.

## Current status

Status checked **2026-08-06** at commit
`6facf0605af5aac09fc6b28ebc1ff4c33af14828`.

| Stage | State | Evidence |
|---|---|---|
| Frozen frontend eval | Complete | 20 tasks, 5 easy / 9 medium / 6 hard |
| Training mix | Complete | 404 records; 384 train / 20 holdout |
| T4-safe bounded split | Complete | 328 train / 18 holdout, whole records only |
| Colab workflow | Complete | Self-contained final notebook, repository and Drive hashes match |
| QLoRA training | Reported complete in active Colab runtime | Final export completion still unconfirmed locally |
| Verified specialist GGUF | Blocked | No local or Drive GGUF found at last check |
| Template verification | Pending | Requires downloaded GGUF and running llama-server |
| Local smoke test | Pending | Requires 10/10 |
| Gate arms A/B/C | Pending | No gate results exist |

**Next task:** run or confirm the final export cell in the active Colab runtime,
capture its `artifact.json` metadata, and finish downloading
`frontend-stack-qwen3-8b-q4_k_m.gguf`.

See [STATUS.md](STATUS.md) for exact resume state and
[training/README.md](training/README.md) for the operational runbook.

## Safety constraint

**Do not train this model locally.** Sustained QLoRA on the local RTX 4060 caused an
NVIDIA `nvlddmkm.sys` bugcheck. Use the guarded Colab T4 workflow. Local GPU use begins
only after the GGUF exists and is limited to inference, template verification, smoke
testing, and gate runs.

## Repository map

```text
datasets/    Curated trajectories, final train/holdout mix, bounded split, manifests
evals/       Frozen real-repository tasks and recorded probe/gate results
notebooks/   Final self-contained Colab QLoRA and Q4_K_M export workflow
plan/        Current v1 execution plan plus historical research
prompts/     Historical teacher, judge, batch, and frontend convention contracts
scripts/     Dataset checks, local verification, guard proxy, smoke test, gate runner
training/    Pinned pi tool schemas, Qwen3 template, and operational runbook
outputs/     Ignored local artifacts and evaluation runs
```

## Fixed experiment

Training input:

- Base: `unsloth/Qwen3-8B`
- Method: 4-bit BitsAndBytes QLoRA, LoRA rank 16, alpha 32
- Context: 4,096 tokens
- Data: 328 whole training records and 18 whole holdout records
- No truncation of trajectories, messages, tool calls, or tool results
- Assistant responses are targets; system, user, and tool messages remain context
- Tool contract: pi's `read`, `bash`, `edit`, `write`, `grep`, `find`, and `ls`

Release comparison:

| Arm | Model | Question |
|---|---|---|
| A | Trained frontend-stack Qwen3-8B Q4_K_M | Does specialist work? |
| B | Stock Qwen3-8B Q4_K_M | Did training improve the base? |
| C | Stock Qwen3-Coder-30B-A3B Q4_K_M | Is specialist competitive with larger generalist? |

All arms use the same 20 frozen tasks, Neura/pi harness, guard proxy, quantization
family, and scoring rules. Arm B is mandatory: A versus B measures training effect;
A versus C measures model-size competitiveness.

## Reproducibility anchors

- Notebook:
  `notebooks/frontend_stack_qwen3_8b_colab.ipynb`
- Notebook SHA-256:
  `87355EDDA48F2425AADB2698B505685020CDAECB618B9EF8AEDBBEF6C6FCAE86`
- Bounded-data manifest:
  `datasets/frontend-stack/final/train-short4096.manifest.json`
- Pinned template:
  `training/templates/qwen3-8b.jinja`
- pi tool schemas:
  `training/pi_tools.json`

## Integrity rules

- Frozen eval tasks never enter training, prompts, or rubric examples.
- `holdout*.jsonl` tracks validation loss; it is not the frozen gate.
- Generation prompts and batch specifications are historical provenance. Do not edit
  them to describe current operations.
- Every exported GGUF must have a `GGUF` header, byte count, SHA-256, and declared
  `Q4_K_M` quantization before evaluation.
- Broken tool JSON or a materially lower tool-validity rate invalidates capability
  comparisons until the train/serve mismatch is fixed.
