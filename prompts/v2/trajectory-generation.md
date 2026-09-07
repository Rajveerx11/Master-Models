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

## Execution evidence and semantic hardening

- Collect tool results from an actual isolated run. The teacher may propose actions
  and explain observed results; it must not author the results itself.
- Save a sidecar run bundle containing source/dependency revisions, actual tool
  events, stdout/stderr, exit codes, final patch and hashes. Exit-code metadata by
  itself is not proof of execution. Do not backfill it into V1 transcripts.
- Read enough context to establish exact, unique, non-overlapping edit targets.
  A tool reporting success cannot excuse an impossible target or invalid final JSX.
- Capture a failing baseline before claiming a failure predates the patch. For an
  unrelated failing suite, preserve the disclosure and run focused checks separately.
- Verify after the last mutation. Typechecking does not prove layout, animation,
  keyboard behavior, server acceptance, or the absence of side effects.
- Check the explanation against language/framework behavior, not just the patch:
  index keys reuse positions; CSS cascade is not HTML class order; Date relational
  comparison is numeric; aria-current=false does not mean current. A natural-looking
  story around a plausible fix is grounds for rejection when causality is false.
- Review the whole candidate pool, including high judge scores. Use source-task
  grouping for splits and independent semantic review before marking final records.

## Rejection triggers

- any eval commit, prompt, or solution overlap;
- impossible file content or edit context;
- tool call without its contiguous result;
- successful-check claim without exit-code-zero evidence;
- broad rewrite, tutorial prose, or theatrical recovery;
- generic review/security advice without exact code evidence.
