# Task 10 - Neutralize hostile Git configuration

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `ee4ead6de81a188594ca4c5fab2d58f24fc144e0`
Start commit: `f9ea18352d9ba908382f4e99c2e8834390a4e1cb`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Read-only Git inspection in Plan mode can still launch pagers, hooks, signature helpers, filesystem monitors, text converters, external diffs, filters, or lazy network fetches supplied by repository configuration. Define one exact hardened invocation prefix and narrow subcommand grammars for object, ref, index, and path reads. Reject unsafe revisions, hidden secret paths, output-producing options, and configuration overrides.

## Success criteria (checkable)

- [ ] Allowed Git commands require a fixed no-pager, no-hook, no-monitor, no-signature, no-mailmap, no-lazy-fetch prefix
- [ ] Diff, log, show, rev-parse, ls-files, and branch accept only explicitly supported read forms
- [ ] External helpers, unsafe refs/tree paths, secret objects, output files, status side effects, and prefix overrides are denied
- [ ] A hostile local hook is proven not to run and the full harness passes

## Verification commands

`node scripts/verify-harness.mjs`

## Scoring: pass / partial / fail notes

- **pass** - hostile Git configuration is neutralized and the precise safe read subset remains usable.
- **partial** - main helpers are disabled but a parser, ref, path, or override gap remains.
- **fail** - repository-controlled code can run, unsafe objects can be read, or harness fails.

## Graders-only reference evidence

Reference solution: `git -C "C:\Neura" show ee4ead6de81a188594ca4c5fab2d58f24fc144e0` (graders only - never shown to a model).

The reference adds a fixed Git prefix, strict revision/tree-path validators, subcommand parsers, and hostile-hook regression probes.
