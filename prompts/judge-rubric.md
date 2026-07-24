# Judge Rubric (Fable 5 as judge)

Purpose: score every generated trajectory 0–10; keep top ~30%. Judge runs in a
SEPARATE conversation from generation (no shared context, no self-leniency).

## Prompt template

```
You are a strict data-quality judge. Score this training trajectory 0-10.
Be harsh: the median trajectory should score 5. Reserve 8+ for flawless.

TRAJECTORY:
{ONE_JSONL_OBJECT}

Score each dimension 0-2, sum = final score:

1. TOOL CORRECTNESS: every tool_call is valid JSON, right tool for the step,
   realistic arguments, no hallucinated tools. (0 = any malformed call)
2. TRAJECTORY LOGIC: steps follow (read before edit, verify after change);
   tool results actually inform the next action; recovery from errors is sane.
3. CODE QUALITY: final code is correct, idiomatic, matches the stated
   conventions, would pass review.
4. TASK REALISM: task is something a real developer asks; scope matches a
   5-40 line diff; not toy, not padded.
5. DIVERSITY VALUE: not a near-duplicate of common patterns; teaches something
   the obvious cases don't.

Automatic 0 (reject regardless of other scores) if:
- any tool call is malformed JSON
- the assistant answers without using tools
- file contents in tool results contradict themselves across turns
- the final code would not run/compile

Output JSON only: {"score": N, "reject_reason": "<or null>", "weakest_dimension": "<name>"}
```

## Process

1. Judge every raw trajectory (batch 20-50 per request).
2. Keep top ~30% by score; hard-reject all automatic-0s regardless of volume.
3. Human spot check: 100 random survivors per domain.
   - If >10% of the spot check is bad → tighten the rubric's weak dimension and
     RE-JUDGE the whole pool. Do not hand-rescue individual examples.
4. Log kept/rejected counts per topic-matrix cell — cells with high reject rates
   get regenerated with a fixed prompt, not padded from other cells.
