# Task 17 - Reverse patch breaks artifact generation contracts

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `7875fc1a706f07c491d8c620623d6484541b2035`
Start commit: `d46f1bbf7c5e44a76e08b1696032b6d8273931ae`
Difficulty: **hard**
Task mode: **review**
Patch files: `apps/desktop/src-tauri/capabilities/default.json`, `apps/desktop/src-tauri/src/commands/artifacts.rs`, `apps/desktop/src-tauri/src/commands/generation.rs`, `apps/desktop/src-tauri/src/providers/embeddings/ollama.rs`, `apps/desktop/src-tauri/src/repositories/artifact_repo.rs`, `apps/desktop/src-tauri/src/services/generation_service.rs`, `apps/desktop/src/components/layout/toolbar.tsx`
Patch base: `7875fc1a706f07c491d8c620623d6484541b2035`
Patch target: `d46f1bbf7c5e44a76e08b1696032b6d8273931ae`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies the snake_case versus kebab-case artifact-type mismatch across the Rust IPC and renderer schema
- [ ] Review identifies that an empty generation scope retrieves no project chunks, producing ungrounded or unusable output
- [ ] Findings cite both sides of each contract and propose compatible serialization plus an effective default retrieval scope

## Verification commands

`cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml && pnpm --filter @testing-ide/desktop typecheck && pnpm --filter @testing-ide/desktop test`

## Scoring: pass / partial / fail notes

- **pass** - reports both independently proven regressions with precise evidence and no false positives.
- **partial** - reports only one regression or gives incomplete trigger/impact analysis.
- **fail** - misses both defects, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **two findings expected**.

Reference solution: `git -C "C:\Testing IDE" show 7875fc1a706f07c491d8c620623d6484541b2035` (graders only - never shown to a model).

The reverse patch serializes artifact variants such as test cases in snake_case while the renderer contract accepts kebab-case, breaking IPC round trips. It also lets an empty scope select zero indexed chunks instead of using the project-wide retrieval default.
