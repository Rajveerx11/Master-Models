# Task 09 - Parse Plan shell filesystem arguments

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `60232e92d47ca63fb9d54eb3672cecdc38b15de8`
Start commit: `4f7e7642290065721acaaf8457f7e7c4dc6c32a7`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Plan mode allows a small set of read-only shell commands, but checking only the executable name misses paths hidden in positional arguments, named parameters, attached option values, and Git pathspecs. Build strict argument recovery for the supported PowerShell, ripgrep, and Git forms. Reject ambiguous parsing, expansions, writes, following links, unsupported abbreviations, and any recovered path outside the project.

## Success criteria (checkable)

- [ ] Quoted tokens, exact PowerShell parameters, ripgrep flags, and Git path arguments are parsed without executing a shell
- [ ] Every recovered filesystem argument is canonicalized and checked against the workspace
- [ ] Ambiguous syntax, arrays, splatting, expansion, link following, writes, and unsupported options fail closed
- [ ] A broad allow/deny matrix passes through `node scripts/verify-harness.mjs`

## Verification commands

`node scripts/verify-harness.mjs`

## Scoring: pass / partial / fail notes

- **pass** - supported forms remain useful and every ambiguous or outside path is denied.
- **partial** - major commands are parsed but option or ambiguity coverage has holes.
- **fail** - parser can be bypassed, invokes shell parsing, or blocks ordinary in-project inspection.

## Graders-only reference evidence

Reference solution: `git -C "C:\Neura" show 60232e92d47ca63fb9d54eb3672cecdc38b15de8` (graders only - never shown to a model).

The reference implements explicit token and option parsers in `action-policy.ts` and adds roughly ninety harness assertions spanning allowed, denied, alias, and junction cases.
