# Teacher Generation Prompt (Fable 5)

Purpose: expand 50–100 seed pairs into 5–10K multi-turn agentic trajectories per
domain. Run in batches (e.g. 25 trajectories per request), varying the topic matrix
per batch. NEVER include any task from `evals/tasks/` (frozen holdout).

## Prompt template

```
You are generating training data for a small local coding model that must operate
as an agent inside a tool-calling harness (read/write files, bash, search, MCP).

DOMAIN (tight scope): {DOMAIN_SCOPE}
  e.g. "React 18 + TypeScript + Tailwind + our component conventions (see style
  guide below)"

STYLE GUIDE / CONVENTIONS:
{PASTE_PROJECT_CONVENTIONS}
  For frontend-stack: paste prompts/frontend-design-conventions.md (distilled from
  taste-skill, ui-ux-pro-max, impeccable) + any project-specific overrides.
  Generated code AND final states must obey it — it is what the specialist learns.

GOLD EXAMPLES (match this quality and format exactly):
{3_SEED_EXAMPLES_JSONL}

TOPIC FOR THIS BATCH: {ROW_FROM_TOPIC_MATRIX}
  e.g. "form validation states" × "medium difficulty" × "bug fix"

Generate {N} training examples as JSONL, one object per line, schema:
{"messages": [
  {"role": "system", "content": "<short harness system prompt>"},
  {"role": "user", "content": "<realistic task>"},
  {"role": "assistant", "tool_calls": [{"name": "read_file", "arguments": {...}}]},
  {"role": "tool", "name": "read_file", "content": "<realistic file content>"},
  ... more tool turns (3-8 turns typical: read -> edit -> verify) ...
  {"role": "assistant", "content": "<final summary of what was done>"}
]}

Hard requirements:
- Every trajectory USES TOOLS. No pure-chat answers.
- Tool calls are valid JSON, realistic arguments, realistic tool results
  (including occasional errors the assistant must recover from — 1 in 5).
- Code follows the style guide above exactly.
- Tasks are the size a real dev asks: not toy, not epic. 5-40 line diffs.
- Vary file names, project shapes, phrasing. No two tasks alike.
```

## Topic matrix (frontend-stack example — build one per domain)

Cross these axes; one cell = one batch:

- **Feature area:** forms · tables/lists · modals/overlays · routing · state mgmt ·
  styling/layout · animations · accessibility · data fetching · error states
- **Task type:** build new · bug fix · refactor · extend existing · review-and-fix ·
  design-polish (working-but-plain UI gets states/a11y/motion per conventions file)
- **Difficulty:** easy (1-2 tool turns) · medium (3-5) · hard (6-8, with a failing
  test or tool error to recover from)

10 × 5 × 3 = 150 cells × ~40 trajectories = 6,000 raw per domain.

## Mix requirements for the final training set (post-filter)

- ~60% domain trajectories (ours, above)
- ~15-20% general tool-calling data (open datasets fine here — protects tool JSON)
- ~20-30% general instruction data (protects reasoning; documented anti-forgetting floor)
