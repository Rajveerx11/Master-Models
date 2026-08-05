"""Embed the frozen training payload into the Colab notebook.

This removes Google Drive and GitHub availability from notebook startup.  Drive
remains an opt-in output target; the default runs entirely in the Colab runtime.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "notebooks/frontend_stack_qwen3_8b_colab.ipynb"
PEFT_FIX_CELL = ROOT / "notebooks/colab_cell_5_peft_fix.py"
MEMORY_SAFE_CELL = ROOT / "notebooks/colab_cell_4_memory_safe.py"
GGUF_EXPORT_CELL = ROOT / "notebooks/colab_cell_8_gguf_export_fix.py"
SOURCE_COMMIT = "0de1e5e87782ec6ec4ece287aa93ba80e20cadfd"
REVISION = "2026-08-06-self-contained-v8-gguf-fix"
PAYLOAD_FILES = (
    Path("datasets/frontend-stack/final/train.jsonl"),
    Path("datasets/frontend-stack/final/holdout.jsonl"),
    Path("training/pi_tools.json"),
    Path("training/templates/qwen3-8b.jinja"),
)


def source_lines(text: str) -> list[str]:
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return lines


def make_payload() -> tuple[bytes, dict[str, str]]:
    buffer = io.BytesIO()
    hashes: dict[str, str] = {}
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in PAYLOAD_FILES:
            data = (ROOT / relative).read_bytes()
            name = relative.as_posix()
            hashes[name] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(name, date_time=(2026, 8, 5, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue(), hashes


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    if len(notebook.get("cells", [])) < 9:
        raise SystemExit("unexpected notebook structure")

    payload, hashes = make_payload()
    payload_b64 = base64.b64encode(payload).decode("ascii")
    payload_b64_wrapped = "\n".join(
        payload_b64[index:index + 120] for index in range(0, len(payload_b64), 120)
    )
    payload_sha = hashlib.sha256(payload).hexdigest()

    notebook["cells"][0]["source"] = source_lines(
        """# Frontend-stack specialist — Qwen3-8B QLoRA

Self-contained Colab workflow: the frozen dataset, tool schemas, and pinned chat template are embedded in this notebook. It does **not** clone GitHub. Google Drive is opt-in, so a failed Drive mount cannot block training.

Choose **Runtime → Change runtime type → GPU**, then **Run all**. A T4 (16 GB) is the minimum; L4/A100 is better. The default uses temporary Colab storage and automatically starts the final GGUF download. Set `USE_GOOGLE_DRIVE = True` in cell 3 only when Drive mounting works.
"""
    )

    notebook["cells"][2]["source"] = source_lines(
        f"""import json, os, platform, subprocess, time
from pathlib import Path
# Apply Unsloth patches before importing torch/transformers/TRL. Conservative chunking lowers peak VRAM.
os.environ.setdefault('UNSLOTH_CE_LOSS_TARGET_GB', '0.05')
os.environ.setdefault('UNSLOTH_DISABLE_DOUBLE_BUFFER', '1')
os.environ.setdefault('PYTORCH_ALLOC_CONF', 'expandable_segments:True')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')
import unsloth
import torch
from importlib.metadata import version
EXPECTED_PACKAGES = {{'unsloth': '2026.5.8', 'unsloth_zoo': '2026.5.4', 'transformers': '4.57.6', 'trl': '0.23.1', 'bitsandbytes': '0.49.2', 'datasets': '4.3.0', 'peft': '0.18.1', 'accelerate': '1.13.0', 'huggingface_hub': '0.36.2', 'tokenizers': '0.22.2', 'safetensors': '0.7.0'}}
PACKAGE_VERSIONS = {{name: version(name) for name in EXPECTED_PACKAGES}}
if PACKAGE_VERSIONS != EXPECTED_PACKAGES: raise RuntimeError(f'Package version mismatch: expected {{EXPECTED_PACKAGES}}, got {{PACKAGE_VERSIONS}}')
print('Pinned packages:', PACKAGE_VERSIONS)

if not torch.cuda.is_available():
    raise RuntimeError('No CUDA GPU. Select Runtime → Change runtime type → GPU, then run all.')
gpu = torch.cuda.get_device_properties(0)
vram_gib = gpu.total_memory / 1024**3
print(f'GPU: {{gpu.name}} | VRAM: {{vram_gib:.2f}} GiB | CUDA: {{torch.version.cuda}}')
if vram_gib < 14.5:
    raise RuntimeError(f'{{vram_gib:.2f}} GiB is insufficient for the guarded 4K run; reconnect to a T4/L4/A100 runtime.')

# Keep this False when Drive authentication is unreliable. Training then runs without any mount prompt.
USE_GOOGLE_DRIVE = False
NOTEBOOK_REVISION = '{REVISION}'
DRIVE_MOUNT = Path('/content/drive')
DRIVE_AVAILABLE = False
if USE_GOOGLE_DRIVE:
    from google.colab import drive
    try:
        drive.mount(str(DRIVE_MOUNT), force_remount=True, timeout_ms=300_000)
        DRIVE_AVAILABLE = (DRIVE_MOUNT / 'MyDrive').is_dir()
        if not DRIVE_AVAILABLE: raise RuntimeError('Drive reported success but MyDrive is unavailable')
    except Exception as mount_error:
        print(f'WARNING: Google Drive mount failed: {{mount_error}}')
        print('Continuing in temporary runtime storage; no retry or crash.')
DRIVE_ROOT = ((DRIVE_MOUNT / 'MyDrive') if DRIVE_AVAILABLE else Path('/content')) / 'Master-Models-Colab/frontend-stack-qwen3-8b'
TRAINER_OUT = DRIVE_ROOT / 'trainer'
LORA_OUT = DRIVE_ROOT / 'lora'
GGUF_OUT = DRIVE_ROOT / 'gguf'
for path in (TRAINER_OUT, LORA_OUT, GGUF_OUT): path.mkdir(parents=True, exist_ok=True)
print(('Persistent Drive output:' if DRIVE_AVAILABLE else 'TEMPORARY runtime output:'), DRIVE_ROOT)
print('Notebook revision:', NOTEBOOK_REVISION)
"""
    )

    notebook["cells"][3]["source"] = source_lines(
        f"""# Restore the frozen project payload embedded in this notebook. No git clone or network archive is used.
import base64, hashlib, io, shutil, zipfile
REPO_COMMIT = '{SOURCE_COMMIT}'
WORK = Path('/content/Master-Models')
PAYLOAD_SHA256 = '{payload_sha}'
PAYLOAD_HASHES = {json.dumps(hashes, sort_keys=True)}
PAYLOAD_B64 = '''{payload_b64_wrapped}'''

payload = base64.b64decode(''.join(PAYLOAD_B64.split()), validate=True)
if hashlib.sha256(payload).hexdigest() != PAYLOAD_SHA256:
    raise RuntimeError('Embedded payload checksum mismatch; upload a fresh notebook copy.')
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    expected = set(PAYLOAD_HASHES)
    actual = {{info.filename for info in archive.infolist() if not info.is_dir()}}
    if actual != expected: raise RuntimeError(f'Embedded payload file list mismatch: {{actual ^ expected}}')
    for info in archive.infolist():
        if info.is_dir(): continue
        destination = (WORK / info.filename).resolve()
        if WORK.resolve() not in destination.parents: raise RuntimeError(f'Unsafe payload path: {{info.filename}}')
        data = archive.read(info)
        if hashlib.sha256(data).hexdigest() != PAYLOAD_HASHES[info.filename]:
            raise RuntimeError(f'Embedded file checksum mismatch: {{info.filename}}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)

template_path = WORK / 'training/templates/qwen3-8b.jinja'
print('Embedded source:', REPO_COMMIT)
print('Payload SHA256:', PAYLOAD_SHA256)
print('Restored files:', len(PAYLOAD_HASHES))
"""
    )

    notebook["cells"][4]["source"] = source_lines(
        MEMORY_SAFE_CELL.read_text(encoding="utf-8")
    )

    notebook["cells"][5]["source"] = source_lines(
        PEFT_FIX_CELL.read_text(encoding="utf-8")
    )

    notebook["cells"][8]["source"] = source_lines(
        GGUF_EXPORT_CELL.read_text(encoding="utf-8")
    )

    notebook["cells"][9]["source"] = source_lines(
        """## Outputs

Default: temporary `/content/Master-Models-Colab/frontend-stack-qwen3-8b/`; the final cell automatically starts the GGUF download. Keep the Colab tab open until it finishes.

With `USE_GOOGLE_DRIVE = True`: `MyDrive/Master-Models-Colab/frontend-stack-qwen3-8b/`.

- `trainer/`: two latest resumable checkpoints
- `lora/`: final adapter and exact tokenizer/template
- `gguf/frontend-stack-qwen3-8b-q4_k_m.gguf`: final model
- `TRAINING_COMPLETE.json`, `SMOKE_TEST.json`, and `gguf/artifact.json`: training, smoke-test, and SHA-256 metadata
"""
    )

    NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {NOTEBOOK}")
    print(f"revision: {REVISION}")
    print(f"payload: {len(payload):,} bytes, sha256={payload_sha}")


if __name__ == "__main__":
    main()
