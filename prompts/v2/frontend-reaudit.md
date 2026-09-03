# Frontend V1-to-V2 semantic re-audit

Review every score-7 row listed in
`datasets/frontend-stack/v2/review/score7-reaudit.jsonl`.

Set all five checks:

1. tool trace is internally consistent;
2. edit context exists in prior read output;
3. verification claims have matching tool evidence;
4. final summary states only observed facts;
5. decision is `keep`, `repair`, or `drop`.

Use `repair` only when code and tool results are correct and the defect is limited to
the final explanation. Use `drop` when code, tool output, or causality is invented.
Do not rewrite a broken trace into a plausible one.
