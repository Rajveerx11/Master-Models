# Code-review frozen-task contract

Code review needs patch inputs, not an instruction to repair a repository.

## Defective tasks

Use a real corrective commit and present its exact reverse patch:

- source/reference commit: known fix;
- patch base: reference commit;
- patch target: reference commit's parent;
- direction: `defective-reverse`.

The patch therefore reintroduces a proven defect. The model sees only the patch and
repository context, never commit messages or reference evidence.

## Clean controls

Use a separate focused corrective commit in its normal direction:

- patch base: reference commit's parent;
- patch target: reference commit;
- direction: `clean-forward`.

The expected answer has no correctness finding. Minor style opinions count as false
positives.

## Frozen set

- 20 unique commits: 16 defective reverse patches and 4 clean controls.
- Difficulty balance: 5 easy, 9 medium, 6 hard.
- Every task identifies exact files, an objective expected finding or clean outcome,
  and graders-only evidence.
- No selected commit or parent may appear in another specialist's eval or any training
  dataset.

The future gate runner must materialize `git diff <base> <target> -- <paths>` and pass
that diff to the model without the commit hashes or subjects.
