# Frontend-stack training and evaluation runbook

This is the canonical operational path from Colab training to the three-arm gate.
Current resume state lives in `STATUS.md`.

## Non-negotiable safety rule

**Do not run sustained QLoRA on the local RTX 4060.** The previous local run caused an
NVIDIA `nvlddmkm.sys` bugcheck. `scripts/train_qlora.py` and
`scripts/export_gguf.py` remain reproducibility/reference tools, not the approved path
for this machine.

Train and export in Google Colab. Use local hardware only for GGUF inference and
evaluation.

## Canonical notebook

File: `notebooks/frontend_stack_qwen3_8b_colab.ipynb`

SHA-256: `87355EDDA48F2425AADB2698B505685020CDAECB618B9EF8AEDBBEF6C6FCAE86`

Revision: `2026-08-06-self-contained-v8-gguf-fix`

The notebook is standalone. It embeds the frozen source train/holdout files, pi tool
schemas, and pinned Qwen3 template. It does not clone this repository.

Approved runtime:

- Colab GPU runtime
- T4 16 GiB minimum; L4/A100 acceptable
- fresh runtime with at least 10 GiB free VRAM before model load
- default `USE_GOOGLE_DRIVE = False`

Default output root is temporary Colab storage:
`/content/Master-Models-Colab/frontend-stack-qwen3-8b/`. The final cell starts a
browser download. With `USE_GOOGLE_DRIVE = True`, output root becomes
`MyDrive/Master-Models-Colab/frontend-stack-qwen3-8b/`.

## Fixed recipe

| Setting | Value |
|---|---|
| Base | `unsloth/Qwen3-8B` |
| Quantized load | BitsAndBytes 4-bit |
| Context | 4,096 tokens |
| Train / holdout | 328 / 18 whole records |
| LoRA | rank 16, alpha 32, dropout 0 |
| Target modules | attention and MLP projection layers |
| Epochs | 2 |
| Learning rate | `2e-4`, cosine, 5% warmup |
| Effective batch | 16 |
| Optimizer | `paged_adamw_8bit` |
| Seed | 731 |
| Targets | assistant responses only |
| Export | GGUF `Q4_K_M` |

The notebook filters the committed 384/20 source split at render time. A record passes
only when the exact pinned-template rendering plus TRL terminal token fits 4,096.
Nothing inside a record is truncated.

Every tool-bearing record passes both `messages` and top-level `tools` to
`apply_chat_template`. Dropping `tools` removes the `<tools>` block and silently trains
against the wrong serving prompt.

## Resume and export in Colab

For a fresh run, select **Runtime → Change runtime type → GPU**, then **Run all**.

For the current run, inspect before rerunning:

- `TRAINING_COMPLETE.json` proves training completed.
- `lora/` contains final adapter and tokenizer/template.
- `SMOKE_TEST.json` contains two cheap pre-export checks.
- `gguf/artifact.json` proves final GGUF verification.

If training is complete but export status is uncertain, run only the final export cell.
It searches both Unsloth locations, including `<save_directory>_gguf`, and reuses
exactly one valid existing Q4_K_M file. With no valid prior file, it removes only known
temporary export directories and performs one clean conversion.

Successful final-cell evidence:

- final filename `frontend-stack-qwen3-8b-q4_k_m.gguf`;
- file larger than 1 GiB;
- first four bytes equal `GGUF`;
- copied byte count equals source byte count;
- SHA-256 printed and stored in `gguf/artifact.json`;
- `quantization` equals `Q4_K_M`;
- temporary export directories cleaned;
- browser download started, or Drive sync reported.

Keep the Colab tab open until download completes.

## Local artifact verification

Place the downloaded model under the ignored output tree:

```powershell
New-Item -ItemType Directory -Force -Path 'outputs\frontend-stack\gguf'
Move-Item -LiteralPath 'C:\Users\rajve\Downloads\frontend-stack-qwen3-8b-q4_k_m.gguf' -Destination 'outputs\frontend-stack\gguf\frontend-stack-qwen3-8b-q4_k_m.gguf'
$specialist = (Resolve-Path 'outputs\frontend-stack\gguf\frontend-stack-qwen3-8b-q4_k_m.gguf').Path
Get-Item -LiteralPath $specialist | Select-Object FullName,Length
Get-FileHash -Algorithm SHA256 -LiteralPath $specialist
Get-Content -LiteralPath $specialist -Encoding Byte -TotalCount 4 | Format-Hex
```

Compare size and SHA-256 with Colab `artifact.json`. Hex output must begin with
`47 47 55 46` (`GGUF`). Stop if any value differs.

## Start serving stack

Use dedicated gate ports: llama-server on 18081, guard proxy on 18080. Keep each
long-running command in its own PowerShell window.

Start llama-server:

```powershell
llama-server -m $specialist --host 127.0.0.1 --port 18081 --jinja
```

Confirm direct server-template compatibility:

```powershell
python scripts/verify_server_template.py --server http://127.0.0.1:18081 --report outputs/frontend-stack/template-verification.json
```

Pass condition: `json_whitespace_normalized_match` is `true`. An exact mismatch caused
only by JSON whitespace is expected across Python Jinja and llama.cpp minja; any other
difference fails qualification.

Verify guard logic:

```powershell
python -m unittest scripts.test_gate_proxy
```

Start proxy:

```powershell
python scripts/gate_proxy.py --host 127.0.0.1 --port 18080 --upstream http://127.0.0.1:18081 --log outputs/frontend-stack/gate-proxy-specialist.jsonl
```

The proxy applies the same two harness guards to every arm: malformed Qwen tool-call
repair/retry and empty tool-result normalization.

## Required 10/10 smoke test

With llama-server and proxy running:

```powershell
python scripts/smoke_model.py --api http://127.0.0.1:18080 --output outputs/frontend-stack/smoke.jsonl
```

All ten cases must pass. They cover read-before-edit behavior, pi `edit` schema, valid
tool JSON, unknown-tool refusal, missing/empty file recovery, arithmetic, general
knowledge, JSON-only output, and a short general explanation.

Do not enter the gate with 9/10. Diagnose template, proxy, or model behavior first.

## Gate prerequisites

Three Q4_K_M artifacts are required:

| Arm | Artifact |
|---|---|
| A | trained `frontend-stack-qwen3-8b-q4_k_m.gguf` |
| B | stock Qwen3-8B Q4_K_M from the same base family |
| C | stock Qwen3-Coder-30B-A3B Q4_K_M |

Also required:

- source repositories referenced by frozen tasks at their recorded paths;
- `pnpm` and lockfile-compatible dependency installation;
- pi launcher at `%APPDATA%\npm\pi.cmd` or explicit `--pi` path;
- `C:\Neura` Git checkout;
- fixed Neura configuration for all arms;
- ports 18080 and 18081 free before each model launch.

## Run arms A, B, and C

`run_gate.py` does not start llama-server. For each arm:

1. Stop previous proxy and server.
2. Start llama-server on 18081 with that arm's GGUF and `--jinja`.
3. Start a fresh proxy on 18080 with an arm-specific log.
4. Set `$modelPath` to the exact GGUF being served.
5. Run the matching command.

```powershell
$modelPath = (Resolve-Path 'outputs\frontend-stack\gguf\frontend-stack-qwen3-8b-q4_k_m.gguf').Path
python scripts/run_gate.py --arm A --tasks all --model-path $modelPath --server-url http://127.0.0.1:18080
```

Repeat with `--arm B` and `--arm C` after relaunching the serving stack with each stock
model. Never claim a different `--model-path` from the model actually loaded upstream.

The runner creates isolated depth-1 checkouts at each task's recorded start commit,
installs frozen dependencies, invokes Neura/pi, records tool metrics, archives patches,
runs TypeScript checking, and leaves `grade` as `ungraded`. It never edits source
repositories.

Resume a matching interrupted arm with the same model and task selection:

```powershell
python scripts/run_gate.py --arm A --tasks all --model-path $modelPath --server-url http://127.0.0.1:18080 --resume
```

An incomplete task directory without `result.json` requires inspection; the runner
will not overwrite it.

## Grade and report

Grade every task `pass`, `partial`, or `fail` against its frozen success criteria.
Record tool-call validity and right-tool use. Then write one consolidated report:

`evals/results/<date>-frontend-stack-vs-baseline.md`

Interpret A versus B first. Interpret A versus C second. Decision matrix lives in
`plan/v1-release-plan.md`.
