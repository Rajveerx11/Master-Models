# V2 Colab training runbook

V2 targets Qwen3-4B because QLoRA and export must fit a free Colab runtime reliably.
This file defines the intended recipe; training stays blocked until a domain has a
frozen eval, validated corpus, and pinned 4B chat template.

## Safety

Do not run sustained QLoRA on the local RTX 4060. A prior run caused an NVIDIA
`nvlddmkm.sys` bugcheck. Local GPU use is limited to GGUF inference and gates.

## Default recipe

| Setting | V2 default |
|---|---|
| Base | `unsloth/Qwen3-4B-bnb-4bit` |
| Export identity | `Qwen/Qwen3-4B` |
| Context | 3,072 tokens; 2,048 fallback |
| Load | 4-bit BitsAndBytes |
| LoRA | rank 16, alpha 32, dropout 0 |
| Target modules | attention and MLP projections |
| Micro-batch | 1 |
| Gradient accumulation | 16 |
| Epochs | 2, with holdout monitoring |
| Learning rate | `2e-4`, cosine, 5% warmup |
| Optimizer | paged AdamW 8-bit |
| Targets | assistant messages only |
| Export | GGUF Q4_K_M |

Do not increase rank, context, batch, or epochs merely because a single runtime has
headroom. Stability and repeatability matter more than consuming all VRAM.

## Runtime storage budget

Start only when Colab has at least 20-25 GB free disk. Keep one base cache, one adapter,
one merged model, and one final GGUF. Delete temporary conversion outputs only after
the GGUF header, size, and SHA-256 are recorded.

## Required inputs per specialist

```text
datasets/<specialist>/v2/final/train.jsonl
datasets/<specialist>/v2/final/holdout.jsonl
datasets/<specialist>/v2/final/train-short3072.jsonl
datasets/<specialist>/v2/final/manifest.json
training/templates/qwen3-4b.jinja
training/pi_tools.json
```

The exact Qwen3-4B template must be pinned from the selected tokenizer revision before
building bounded splits. V1's `qwen3-8b.jinja` is historical and must not be silently
reused even though current 4B/8B families are closely related.

## Colab sequence

1. Install pinned package versions.
2. Verify T4/L4 GPU and free disk/VRAM.
3. Decode or upload the validated bounded split.
4. Load the 4-bit base and assert tokenizer/template hash.
5. Render all records with top-level `tools`; reject any missing `<tools>` block.
6. Run one forward/backward probe on the longest record.
7. Train with checkpoint resume and holdout evaluation.
8. Save adapter and tokenizer.
9. Merge and export one Q4_K_M GGUF.
10. Record artifact metadata, then download or sync to Drive.

## Stop conditions

Stop the run if:

- the live template differs from the pinned template;
- any rendered record exceeds the configured context;
- tool-bearing data renders without tool definitions;
- CUDA OOM repeats after falling back from 3,072 to 2,048;
- holdout loss diverges or generated tool JSON regresses;
- free disk drops below the merge/export requirement.

## After download

Verify GGUF magic bytes, byte count, SHA-256, template behavior, and 10/10 smoke tests.
Then run arm A and stock arm B on the same frozen tasks. Detailed gate rules live in
`evals/README.md`.

V1's 8B notebook remains an archived reproducibility artifact. A parameterized 4B
self-contained notebook is a V2 deliverable after the first final dataset is frozen.
