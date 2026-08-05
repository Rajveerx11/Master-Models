# Frontend-stack specialist status

**Checked:** 2026-08-06  
**Branch:** `master`  
**Checkpoint:** `6facf0605af5aac09fc6b28ebc1ff4c33af14828`  
**Repository state before documentation edits:** clean and synchronized with
`origin/master`

This file is the live resume ledger. Update it after any artifact, verification, smoke,
or gate milestone. Historical generation details belong in `plan/` and `prompts/`.

## Completed

- Frontend-stack eval frozen: 20 real tasks, 5 easy / 9 medium / 6 hard.
- Final source mix built: 404 records, split into 384 train / 20 holdout.
- T4-safe split verified: 328 train / 18 holdout at 4,096 tokens.
- Whole-record filtering used; no trajectory truncation.
- Final self-contained Colab notebook committed and mirrored to Google Drive.
- Repository and Drive notebook hashes match:
  `87355EDDA48F2425AADB2698B505685020CDAECB618B9EF8AEDBBEF6C6FCAE86`.
- Colab workflow includes pinned package checks, fresh-runtime VRAM guard,
  BitsAndBytes-preserving TorchAO bypass, checkpoint resume, pre-export smoke checks,
  corrected Unsloth GGUF discovery, atomic final copy, header/size/hash verification,
  and temporary export cleanup.
- Six guard-proxy unit tests pass.

## Current external state

- Drive notebook:
  `G:\My Drive\Colab Notebooks\frontend_stack_qwen3_8b_colab.ipynb`
- Expected Drive artifact directory:
  `G:\My Drive\Master-Models-Colab\frontend-stack-qwen3-8b`
- Expected final filename:
  `frontend-stack-qwen3-8b-q4_k_m.gguf`
- No GGUF was found under repository `outputs/`, the expected Drive artifact
  directory, or `C:\Users\rajve\Downloads` at this check.
- No gate result exists.
- Colab runtime state cannot be inferred from local files. Export may already have
  completed inside the active runtime.

## Immediate next task

In active Colab runtime:

1. Inspect final export cell output.
2. If incomplete, run only the final export cell. It reuses one valid prior Q4_K_M
   export when present; otherwise it performs one clean export.
3. Confirm printed artifact metadata contains:
   - final path ending in `frontend-stack-qwen3-8b-q4_k_m.gguf`;
   - size greater than 1 GiB;
   - SHA-256;
   - `quantization: Q4_K_M`.
4. Preserve `gguf/artifact.json` or its printed JSON.
5. Keep Colab tab open until browser download finishes.

Do not restart training unless Colab evidence proves training or LoRA output is absent.
Do not train locally.

## Queue after download

- [ ] Move downloaded specialist GGUF into an ignored local artifact directory.
- [ ] Compare local size and SHA-256 with Colab `artifact.json`.
- [ ] Start llama-server with `--jinja` on port 18081.
- [ ] Run server-template verification; normalized match must pass.
- [ ] Start guard proxy on port 18080.
- [ ] Run `scripts/smoke_model.py`; require 10/10.
- [ ] Obtain stock Qwen3-8B Q4_K_M for arm B.
- [ ] Confirm stock Qwen3-Coder-30B-A3B Q4_K_M for arm C.
- [ ] Run and grade arm A.
- [ ] Run and grade arm B.
- [ ] Run and grade arm C.
- [ ] Commit consolidated gate report under `evals/results/`.

Full commands: `training/README.md`. Decision rule: `plan/v1-release-plan.md`.
