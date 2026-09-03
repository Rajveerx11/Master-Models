# Task 08 - Contain Plan-mode file tools

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `fec37397662c178acf6c308b5ed1714afe828d57`
Start commit: `1b0168c2d4542dbcf0471fa0f40233ce6606be18`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Plan mode is intended to inspect only its project, yet read, search, find, and list requests can escape through absolute paths, home aliases, file URLs, junctions, or a nonexistent child below an outside link. Make containment use canonical filesystem identity, including missing descendants, while preserving valid in-project reads. Keep execution-directory and repository-root handling distinct.

## Success criteria (checkable)

- [ ] Relative, absolute, home-alias, tool-alias, and file-URL inputs resolve consistently
- [ ] Existing symlinks or junctions and missing descendants beneath them cannot escape the workspace
- [ ] Read, grep, find, and list tools share the same containment decision and input validation
- [ ] Normal files inside the workspace remain readable and `node scripts/verify-harness.mjs` passes

## Verification commands

`node scripts/verify-harness.mjs`

## Scoring: pass / partial / fail notes

- **pass** - all alias, canonicalization, link, and missing-child cases fail closed outside the workspace.
- **partial** - common escapes close but one alias or missing-path case remains.
- **fail** - any tested outside path is allowed, inside reads break, or harness fails.

## Graders-only reference evidence

Reference solution: `git -C "C:\Neura" show fec37397662c178acf6c308b5ed1714afe828d57` (graders only - never shown to a model).

The reference adds alias-aware resolution, nearest-existing-ancestor canonicalization, workspace-relative facts, and a cross-tool junction test matrix.
