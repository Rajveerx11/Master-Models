# V2 evaluation protocol

Evaluation is the release boundary. A low training loss does not prove a specialist.

## Freeze-before-generate rule

Each specialist needs 20 real repository tasks committed before its training queue is
opened. Every task records:

- source repository and immutable reference commit;
- parent/start commit;
- verbatim agent prompt;
- checkable success criteria;
- verification command;
- graders-only reference evidence;
- easy, medium, or hard difficulty.

All reference commits, patches, prompts, and close paraphrases are excluded from train,
holdout, prompts, and demonstrations. Corrections create a versioned successor set;
frozen tasks are not silently edited.

## Current freeze state

| Specialist | Frozen tasks | State |
|---|---:|---|
| frontend-stack | 20 | Frozen V1 set, reusable for V2 |
| backend-stack | 20 | Frozen V2 set |
| security-review | 20 | Frozen V2 set |
| code-review | 20 | Frozen V2 set |
| testing-qa | 20 | Frozen V2 set |

## Required comparison

Each domain gate uses the same tasks, harness, template, quantization family, context
limit, and scoring rules for both arms.

| Arm | Model | Purpose |
|---|---|---|
| A | trained domain Qwen3-4B Q4_K_M | candidate |
| B | stock Qwen3-4B Q4_K_M | isolates fine-tuning effect |

A larger coding model may be added as a reference arm, but it is not required to prove
that specialization improved the base.

## Qualification

Before the gate, arm A must pass:

- GGUF header, byte count, SHA-256, and declared quantization check;
- training-template versus server-template normalized match;
- structural tool-call tests;
- 10/10 domain smoke suite;
- no eval-overlap report failures.

## Release rule

Ship a specialist only when it:

1. beats stock 4B on pass rate;
2. does not materially reduce tool-call validity;
3. has no critical safety regression;
4. records all results, including failures.

If A ties or loses B, improve data or stop that specialist. Do not hide the result by
changing the frozen set.

## Validation

```powershell
py -3 scripts/validate_eval_tasks.py --require-v2
```

The validator checks task shape, immutable Git ancestry, exact 5/9/6 difficulty
balance, and cross-domain reference/start isolation.
