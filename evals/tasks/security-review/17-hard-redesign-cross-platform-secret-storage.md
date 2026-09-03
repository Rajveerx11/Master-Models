# Task 17 - Redesign cross-platform secret storage

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `a4d62bfe76b805111aab7e245a848fc637ffbdc9`
Start commit: `5c3784d9d06ba8391fb5a4f7ffebd4b78221d3b7`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Secret access currently depends on frontend keyring plumbing that is unreliable on Linux systems without a Secret Service daemon. Move get, set, delete, and batch-read operations behind native Tauri commands with one frontend API. Use platform credential storage where available; on Linux provide an atomic user-only local fallback with stable app-data placement and cached reads. Missing entries should not be treated as fatal errors.

## Success criteria (checkable)

- [ ] Frontend secret operations use native commands with no platform branching or obsolete keyring plugin permission
- [ ] Windows and macOS use OS credential storage; missing entries return `null`/`None`
- [ ] Linux fallback writes only in app-local data with mode 0600, temporary-file replacement, and synchronized cached state
- [ ] Single and batch reads preserve account ordering and do not expose secrets through logs or error messages
- [ ] Tauri command registration, Rust checks, and frontend typecheck pass

## Verification commands

`cargo test --manifest-path src-tauri/Cargo.toml && pnpm exec tsc --noEmit`

## Scoring: pass / partial / fail notes

- **pass** - one reliable cross-platform API uses correct storage, permissions, atomicity, and missing-entry semantics.
- **partial** - main platforms work but Linux safety, batch behavior, registration, or compatibility is incomplete.
- **fail** - secrets use ordinary frontend storage, permissions are broad, writes are non-atomic, or checks fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\terax-ai" show a4d62bfe76b805111aab7e245a848fc637ffbdc9` (graders only - never shown to a model).

The reference creates `src-tauri/src/modules/secrets.rs`, registers four commands and managed state, removes the frontend keyring plugin dependency, and adapts the TypeScript API.
