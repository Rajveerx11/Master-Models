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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "datasets/frontend-stack/final/train.jsonl"
HOLDOUT = ROOT / "datasets/frontend-stack/final/holdout.jsonl"
PINNED_TEMPLATE = ROOT / "training/templates/qwen3-8b.jinja"
OUT = ROOT / "outputs/frontend-stack"  # gitignored

BASE = "unsloth/Qwen3-8B"
MAX_SEQ = 8192  # longest record ~6.2k tokens, p90 ~4.5k

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true",
                    help="run both guards and print one formatted sample, then exit")
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    args = ap.parse_args()

    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import train_on_responses_only

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE,
        max_seq_length=MAX_SEQ,
        load_in_4bit=True,
    )
    check_template(tokenizer)

    rows_train, rows_eval = read_jsonl(TRAIN), read_jsonl(HOLDOUT)
    # `source` is provenance only -- the formatter must not see it as an input.
    def to_ds(rows):
        return Dataset.from_list(
            [{"messages": r["messages"], "tools": r.get("tools")} for r in rows]
        )

    fmt = formatter(tokenizer)
    ds_train = to_ds(rows_train).map(fmt, batched=True, remove_columns=["messages", "tools"])
    ds_eval = to_ds(rows_eval).map(fmt, batched=True, remove_columns=["messages", "tools"])
    print(f"guard 2 ok: {len(ds_train)} train / {len(ds_eval)} holdout formatted")

    if args.check_only:
        sample = next(t for t in ds_train["text"] if "<tools>" in t)
        print("\n----- formatted sample (head) -----\n" + sample[:1500])
        print("\n----- formatted sample (tail) -----\n" + sample[-800:])
        return

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
        tokenizer=tokenizer,
        train_dataset=ds_train,
        eval_dataset=ds_eval,
        args=SFTConfig(
            output_dir=str(OUT),
            dataset_text_field="text",
            max_seq_length=MAX_SEQ,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=16,  # effective batch 16
            num_train_epochs=args.epochs,
            learning_rate=args.lr,
            lr_scheduler_type="cosine",
            warmup_ratio=0.05,
            logging_steps=1,
            eval_strategy="steps",
            eval_steps=10,
            save_strategy="epoch",
            optim="adamw_8bit",
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

    stats = trainer.train()
    print(stats)
    model.save_pretrained(str(OUT / "lora"))
    tokenizer.save_pretrained(str(OUT / "lora"))
    print(f"\nLoRA saved to {OUT / 'lora'}")
    print("Next: merge to 16-bit, export GGUF Q4_K_M, then byte-match the prompt against "
          "llama-server before trusting any eval (training/README.md).")


if __name__ == "__main__":
    main()
