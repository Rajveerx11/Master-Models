# V2 trajectory judge

Score each dimension 0-2. Keep only total scores of 8-10 after deterministic validation.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Tool correctness | invalid/invented | usable but wasteful | exact, minimal, complete |
| Reasoning/trajectory | contradictory | mostly coherent | evidence-led and efficient |
| Domain quality | wrong/unsafe | partial | correct and convention-aware |
| Realism/verification | fabricated | weak check | real focused evidence |
| Coverage value | duplicate/trivial | common pattern | difficult useful gap |

Automatic rejection overrides the numeric score for malformed JSON, eval leakage,
fabricated output, unsupported verification, destructive unrelated changes, or a
reference patch copied into the user prompt.

Judge output must contain the five scores, total, concise evidence, detected risks, and
one of `keep`, `human-review`, or `reject`.
