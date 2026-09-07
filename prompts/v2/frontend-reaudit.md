# Frontend V1-to-V2 semantic re-audit

The 2026-09-06 hardening ledger at
`datasets/frontend-stack/v2/review/hardening/audit.jsonl` screens all scores and
supersedes the score-7-only queue for triage. Its `replay_required` status is not
approval. Do not upgrade authored V1 tool output to captured evidence or invent a
repository/commit for a synthetic task. Review all scores; 8/9 records also had
incorrect explanations. Preserve V1; use separate candidates and real replay logs.

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
