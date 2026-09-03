# V2 implementation-task contract

Every backend, security, and testing/QA task uses this metadata:

```text
# Task NN - Human-readable title

Source repository: `registry-id`
Source checkout: `absolute local path`
Reference commit: `40-character hash`
Start commit: `reference commit's 40-character parent hash`
Difficulty: **easy|medium|hard**
```

Required sections:

- `## Prompt (given to the agent verbatim)`
- `## Success criteria (checkable)` with at least three checkboxes
- `## Verification commands`
- `## Scoring: pass / partial / fail notes`
- `## Graders-only reference evidence`

The prompt must describe the user-visible or engineering problem without commit
subjects, hashes, solution symbols, or reference-patch wording. Reference evidence is
never passed to the model.

Easy means one focused behavior with a narrow patch. Multi-file ownership changes,
new subsystems, migrations, concurrency, or platform-specific lifecycle behavior are
medium or hard.
