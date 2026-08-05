"""Reference local merge/export path for a trained frontend-stack LoRA.

The approved current export runs in the self-contained Colab notebook. Use this script
only in a separately approved Unsloth environment with an existing LoRA:

    python scripts/export_gguf.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LORA = ROOT / "outputs/frontend-stack/lora"
OUT = ROOT / "outputs/frontend-stack/gguf"
PINNED_TEMPLATE = ROOT / "training/templates/qwen3-8b.jinja"
MAX_SEQ = 8192


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", type=Path, default=LORA)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    if not args.lora.is_dir():
        raise SystemExit(f"LoRA directory does not exist: {args.lora}")

    # Unsloth must patch torch/transformers before either is imported elsewhere.
    import unsloth  # noqa: F401
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(args.lora),
        max_seq_length=MAX_SEQ,
        load_in_4bit=True,
    )

    # Model loading replaces Qwen3's template. Export the exact template used to
    # format training records so llama.cpp receives the same prompt contract.
    tokenizer.chat_template = PINNED_TEMPLATE.read_text(encoding="utf-8")
    args.output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained_gguf(
        str(args.output),
        tokenizer,
        quantization_method="q4_k_m",
        maximum_memory_usage=0.75,
    )
    ggufs = sorted(args.output.glob("*.gguf"))
    if not ggufs:
        raise SystemExit(f"GGUF export reported success but wrote no file under {args.output}")
    for path in ggufs:
        print(f"GGUF: {path} ({path.stat().st_size / 1024**3:.2f} GiB)")


if __name__ == "__main__":
    main()
