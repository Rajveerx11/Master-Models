# Task 02 - Contain WSL distro names in UNC paths

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `9d54cdbc949dc8589c0c3fe919d5d497e3314f7b`
Start commit: `82e4f0800ea3356a2329f1c513025f6874c6c869`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

A WSL distribution name is inserted into a Windows UNC path before filesystem access. A locally registered distribution can use path metacharacters to escape the intended share. Validate this component before constructing the path. Preserve common real distribution names, fail closed for malformed names, and add Windows-only unit tests for valid names, traversal attempts, special characters, and the final path.

## Success criteria (checkable)

- [ ] Empty, leading-dot, traversal, slash, backslash, control, and path-metacharacter names are rejected
- [ ] Common alphanumeric names containing spaces, dots, underscores, or hyphens remain accepted
- [ ] An invalid distribution never produces a UNC path containing attacker-controlled traversal
- [ ] `cargo test --manifest-path src-tauri/Cargo.toml workspace::auth_tests` or the equivalent workspace test filter passes on Windows

## Verification commands

`cargo test --manifest-path src-tauri/Cargo.toml workspace`

## Scoring: pass / partial / fail notes

- **pass** - validation prevents share escape, retains legitimate names, and has platform-gated tests.
- **partial** - traversal is blocked but valid-name compatibility or tests are incomplete.
- **fail** - attacker-controlled names still reach UNC construction or Rust checks fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\terax-ai" show 9d54cdbc949dc8589c0c3fe919d5d497e3314f7b` (graders only - never shown to a model).

The reference adds a bounded allowlist validator and returns a fixed invalid share path before interpolation. Tests cover real distro names and traversal payloads.
