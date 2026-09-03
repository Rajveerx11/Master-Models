# Eval candidate queues

These JSONL files are review queues, not frozen eval tasks and not training data.

All four V2 queues have now produced frozen 20-task suites. Keep these files as
selection provenance; do not treat them as current generation inputs.

For each specialist, select 20 reproducible commits with a 5 easy / 9 medium / 6 hard
balance. Confirm the parent revision builds, write a user-facing prompt and objective
checks, then create task Markdown under `evals/tasks/<specialist>/`.

After review:

1. add all 20 task files;
2. change the registry state and count;
3. rebuild source inventories so reference commits and parents are excluded;
4. build the training-generation queue.

The queues intentionally use unique reference and parent commits across specialists
and cap repeated commit scopes. They still require human review; a high inventory
score does not prove a good eval task.
