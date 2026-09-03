# V2 frozen eval authoring

Use one reviewed real Git commit. The model starts at its single parent and never sees
the reference commit.

## Accept only when

- the parent checks out and required dependencies are recoverable;
- the issue can be described without copying the commit message or patch;
- success has objective behavioral or test evidence;
- the change belongs mainly to one specialist;
- the reference patch is focused enough to grade;
- no sibling training record uses the commit or its parent.

Write the task with source repository, full reference hash, full parent hash, difficulty,
verbatim prompt, success checklist, verification command, and graders-only evidence.
Do not include solution hints in the prompt.
