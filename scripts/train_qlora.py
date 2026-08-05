"""QLoRA fine-tune Qwen3-8B on the frontend-stack mix.

    python scripts/train_qlora.py                  # train
    python scripts/train_qlora.py --check-only     # guards + one formatted sample, no training

Run this inside the Unsloth environment (needs torch/transformers/unsloth/trl).
Recipe and rationale: training/README.md. Data manifest:
datasets/frontend-stack/final/MANIFEST.md.

The two guards at the top are the point of this file. Both failure modes they catch are
silent -- training completes, loss looks fine, and tool calling is dead at serve time.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "datasets/frontend-stack/final/train-short4096.jsonl"
HOLDOUT = ROOT / "datasets/frontend-stack/final/holdout-short4096.jsonl"
PINNED_TEMPLATE = ROOT / "training/templates/qwen3-8b.jinja"
OUT = ROOT / "outputs/frontend-stack"  # gitignored

BASE = "unsloth/Qwen3-8B"
MAX_SEQ = 4096  # hard cap enforced by scripts/build_short_train.py

# Qwen3 turn markers. Tool results render as user turns (the template wraps them in
# <|im_start|>user\n<tool_response>), so this masking makes system, user, AND tool turns
# context, and assistant turns the only targets -- exactly what the plan requires.
INSTRUCTION_PART = "<|im_start|>user\n"
RESPONSE_PART = "<|im_start|>assistant\n"


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def check_template(tokenizer) -> None:
    """Guard 1: the tokenizer's template must equal the one the data was built against.

    build_train_mix.py rendered every record through the pinned copy. If Unsloth ships a
    different Qwen3 template, the trained text silently stops matching what was verified.
    """
    pinned = PINNED_TEMPLATE.read_text(encoding="utf-8")
    live = tokenizer.chat_template
    if live is None:
        raise SystemExit("tokenizer has no chat_template; cannot train tool calling")
    if live.strip() != pinned.strip():
        raise SystemExit(
            "chat template MISMATCH between the tokenizer and "
            f"{PINNED_TEMPLATE.relative_to(ROOT)}.\n"
            "Do not train through this. Either re-pin the template and rebuild the data "
            "(python scripts/build_train_mix.py), or pin the tokenizer to the template "
            "the data was built with. Silent template drift is the #1 way this fails."
        )
    print("guard 1 ok: tokenizer template matches the pinned copy")


def pin_template(tokenizer) -> None:
    """Keep training/export on the repository-pinned serving contract.

    Unsloth replaces Qwen3's tokenizer template during model loading. That runtime
    template is close, but not byte-identical to the official template used by the
    dataset build. Restore the pinned copy so formatting and the saved tokenizer use
    one explicit contract instead of whichever template the installed package ships.
    """
    pinned = PINNED_TEMPLATE.read_text(encoding="utf-8")
    live = tokenizer.chat_template
    if live is None or live.strip() != pinned.strip():
        print("runtime tokenizer template differs; restoring the pinned Qwen3 template")
        tokenizer.chat_template = pinned
    check_template(tokenizer)


def formatter(tokenizer):
    """Guard 2: `tools` must reach apply_chat_template.

    Dropping it removes the <tools> block from the prompt. pi always sends tools at serve
    time, so the model would train on a prompt shape it never sees.
    """
    def fmt(batch):
        texts = []
        for msgs, tools in zip(batch["messages"], batch["tools"]):
            text = tokenizer.apply_chat_template(
                msgs,
                tools=tools or None,  # dolly records legitimately have none
                tokenize=False,
                add_generation_prompt=False,
                enable_thinking=False,
            )
            if tools and "<tools>" not in text:
                raise SystemExit(
                    "tools were passed but no <tools> block was rendered -- the template "
                    "is not the tool-calling Qwen3 template."
                )
            texts.append(text)
        return {"text": texts}

    return fmt


def main() -> None:
    # Unsloth status lines contain Unicode symbols. Windows may otherwise expose a
    # CP1252 console and crash before training while printing its trainer summary.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true",
                    help="run both guards and print one formatted sample, then exit")
    ap.add_argument(
        "--probe-longest", action="store_true",
        help="train exactly one optimizer step on the deterministically longest bounded record",
    )
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument(
        "--max-seq", type=int, default=MAX_SEQ,
        help=f"maximum whole-record sequence length (default: {MAX_SEQ})",
    )
    ap.add_argument(
        "--optimizer", default="paged_adamw_8bit",
        help="Trainer optimizer; paged AdamW keeps the first update inside 8 GB VRAM",
    )
    ap.add_argument(
        "--train-file", type=Path, default=TRAIN,
        help="whole-record bounded training JSONL (default: train-short4096.jsonl)",
    )
    ap.add_argument(
        "--holdout-file", type=Path, default=HOLDOUT,
        help="frozen loss-tracking JSONL; frozen task evals are never training input",
    )
    ap.add_argument("--output-dir", type=Path, default=OUT)
    ap.add_argument("--gradient-accumulation-steps", type=int, default=16)
    ap.add_argument(
        "--max-steps", type=int, default=-1,
        help="trainer step cap; useful for a one-step hardware probe",
    )
    ap.add_argument(
        "--resume-from-checkpoint", type=Path,
        help="resume optimizer/trainer state from a checkpoint-* directory",
    )
    ap.add_argument(
        "--ce-loss-target-gb",
        type=float,
        default=0.02,
        help="VRAM budget for each fused cross-entropy chunk (8 GB-safe default)",
    )
    args = ap.parse_args()
    if args.check_only and args.probe_longest:
        ap.error("--check-only and --probe-longest cannot be combined")
    if args.probe_longest:
        if args.max_steps not in (-1, 1):
            ap.error("--probe-longest only supports --max-steps -1 or 1")
        # This is a hardware safety probe, not an equivalently sized training run.
        args.max_steps = 1
        args.gradient_accumulation_steps = 1
    if args.ce_loss_target_gb <= 0:
        ap.error("--ce-loss-target-gb must be positive")
    if args.max_seq <= 0:
        ap.error("--max-seq must be positive")
    if args.gradient_accumulation_steps <= 0:
        ap.error("--gradient-accumulation-steps must be positive")
    # The 8B model leaves almost no reported free VRAM on an 8 GB card. Without an
    # explicit chunk budget Unsloth aborts before step 1 instead of choosing a tiny
    # chunk from the negligible free-memory reading.
    os.environ.setdefault("UNSLOTH_CE_LOSS_TARGET_GB", str(args.ce_loss_target_gb))
    # Unsloth's optional two-buffer CUDA event path can abort the whole Python
    # process on Windows after a long backward pass (rather than raising a
    # catchable exception). Single buffering keeps the same gradients and uses
    # less VRAM; it only gives up overlapping the host-to-device copy.
    os.environ.setdefault("UNSLOTH_DISABLE_DOUBLE_BUFFER", "1")

    # Unsloth patches torch/transformers/TRL at import time. Import it first or the
    # unpatched implementations use more memory, which is especially risky on 8 GB.
    import unsloth  # noqa: F401
    from unsloth import FastLanguageModel, is_bfloat16_supported
    from unsloth.chat_templates import train_on_responses_only
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE,
        max_seq_length=args.max_seq,
        load_in_4bit=True,
    )
    pin_template(tokenizer)

    if not args.train_file.is_file():
        raise SystemExit(
            f"missing bounded training data: {args.train_file}. Run "
            "python scripts/build_short_train.py before training."
        )
    if not args.holdout_file.is_file():
        raise SystemExit(f"missing holdout data: {args.holdout_file}")
    rows_train, rows_eval = read_jsonl(args.train_file), read_jsonl(args.holdout_file)
    fmt = formatter(tokenizer)

    # Render before Arrow conversion. The mixed corpus contains plain messages and
    # structured tool-call messages whose nested fields cannot share one Arrow struct
    # schema. Training consumes only rendered text, so storing those source objects in
    # Dataset would add failure risk without value. `source` remains provenance only.
    def to_ds(rows, label):
        rendered = fmt({
            "messages": [r["messages"] for r in rows],
            "tools": [r.get("tools") for r in rows],
        })
        # TRL appends one terminal <|im_end|> token to text-field examples.  Refuse a
        # custom dataset that would make it silently truncate within a trajectory.
        lengths = [len(tokenizer(text).input_ids) + 1 for text in rendered["text"]]
        if over := [n for n in lengths if n > args.max_seq]:
            raise SystemExit(
                f"{label} contains {len(over)} records above max_seq={args.max_seq} "
                "after the terminal token. Rebuild a whole-record bounded split; do not truncate."
            )
        return Dataset.from_dict(rendered), lengths

    ds_train, train_lengths = to_ds(rows_train, "training data")
    ds_eval, eval_lengths = to_ds(rows_eval, "holdout")
    print(f"guard 2 ok: {len(ds_train)} train / {len(ds_eval)} holdout formatted")

    if args.check_only:
        sample = next(t for t in ds_train["text"] if "<tools>" in t)
        print("\n----- formatted sample (head) -----\n" + sample[:1500])
        print("\n----- formatted sample (tail) -----\n" + sample[-800:])
        return

    if args.probe_longest:
        longest = max(range(len(train_lengths)), key=train_lengths.__getitem__)
        print(
            f"hardware probe: train record {longest + 1}/{len(train_lengths)} "
            f"at {train_lengths[longest]} tokens; one optimizer step, accumulation=1"
        )
        ds_train = ds_train.select([longest])

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        lora_dropout=0.0,
        bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth",
        random_state=731,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=ds_train,
        eval_dataset=ds_eval,
        args=SFTConfig(
            output_dir=str(args.output_dir),
            dataset_text_field="text",
            max_length=args.max_seq,
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            num_train_epochs=args.epochs,
            max_steps=args.max_steps,
            learning_rate=args.lr,
            lr_scheduler_type="cosine",
            warmup_ratio=0.05,
            logging_steps=1,
            eval_strategy="steps",
            eval_steps=10,
            # Preserve a resume point after every optimizer step.  On 8 GB VRAM, a
            # long backward pass may fail late enough that epoch-only saving loses all work.
            save_strategy="steps",
            save_steps=1,
            save_total_limit=2,
            optim=args.optimizer,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            weight_decay=0.01,
            seed=731,
            report_to="none",
        ),
    )

    # Assistant turns are the only targets; system, user, and tool turns are context.
    trainer = train_on_responses_only(
        trainer,
        instruction_part=INSTRUCTION_PART,
        response_part=RESPONSE_PART,
    )

    stats = trainer.train(
        resume_from_checkpoint=(
            str(args.resume_from_checkpoint) if args.resume_from_checkpoint else None
        )
    )
    print(stats)
    model.save_pretrained(str(args.output_dir / "lora"))
    tokenizer.save_pretrained(str(args.output_dir / "lora"))
    print(f"\nLoRA saved to {args.output_dir / 'lora'}")
    print("Next: merge to 16-bit, export GGUF Q4_K_M, then byte-match the prompt against "
          "llama-server before trusting any eval (training/README.md).")


if __name__ == "__main__":
    main()
