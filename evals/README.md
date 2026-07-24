# Evals — the honesty layer

The eval set is the only defense against grading our own homework. Rules:

1. **Written first.** Eval tasks are created and committed BEFORE any seed writing
   or dataset generation for that domain begins. Git history is the proof.
2. **Frozen.** Once committed, tasks never change. Fixes = new versioned set
   (`v2/`), old one stays.
3. **Held out absolutely.** No eval task, paraphrase, or fragment may appear in any
   teacher generation prompt, seed pair, or judge rubric example.
4. **Real, not synthetic.** Tasks come from actual repo history: closed issues,
   real diffs, real bugs. Not invented, not Fable-generated.
5. **Scored in the live harness.** Metric = task completion (does the change work,
   do tests pass), plus tool-call validity rate and right-tool rate. Never
   "answer similarity".
6. **Fixed baseline.** Gate opponent is stock Qwen3-Coder-30B-A3B (Q4_K_M), same
   harness, same tasks, same scoring.

## Layout

```
evals/
  tasks/frontend-stack/   20 frozen tasks (one .md each, template below)
  tasks/backend-stack/
  tasks/code-review/
  results/                gate runs: <date>-<model>-vs-baseline.md
```

## Task template

```markdown
# Task NN — <one-line title>
Source: <repo + issue/commit link or path>
## Prompt (given to the agent verbatim)
...
## Success criteria (checkable)
- [ ] ...
## Scoring: pass / partial / fail notes
```
