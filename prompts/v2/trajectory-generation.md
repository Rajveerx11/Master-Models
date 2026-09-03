# V2 source-grounded trajectory generation

Generate one complete coding-agent trajectory from an approved non-eval source record.
The target is Qwen3-4B, so every step must earn its tokens.

## Input

- specialist ID and coverage tag;
- repository identity, parent commit, reference commit, and changed paths;
- parent-state file contents;
- reference diff for factual grounding;
- exact pi tool schemas;
- permitted verification commands.

## Requirements

1. Write a natural user request that describes the real problem without exposing the
   reference patch.
2. Inspect relevant files before editing or reviewing.
3. Use 2-8 meaningful tool calls. Do not pad the trace.
4. Preserve exact tool outputs. Never invent command, browser, test, or screenshot
   evidence.
5. Prefer the smallest correct change and follow repository conventions.
6. Include a natural failed step only when the source evidence supports one.
7. Run at least one focused verification command.
8. Attach `metadata.exit_code` to every bash result.
9. The final summary may claim only what the tool results prove.
10. Emit exactly one JSON object matching
    `datasets/schema/trajectory-v2.schema.json`.

## Rejection triggers

- any eval commit, prompt, or solution overlap;
- impossible file content or edit context;
- tool call without its contiguous result;
- successful-check claim without exit-code-zero evidence;
- broad rewrite, tutorial prose, or theatrical recovery;
- generic review/security advice without exact code evidence.
