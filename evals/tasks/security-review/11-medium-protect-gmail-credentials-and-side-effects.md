# Task 11 - Protect Gmail credentials and side effects

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `2db30d98ad32e5a9466753d566ef7b8ebfe80098`
Start commit: `06949914fac24687565ba9b617416114e6f59e11`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Add Gmail through the existing MCP bridge without storing a credential in tracked files or exposing it to arbitrary subprocesses. Read-only mailbox actions should remain frictionless. Sending, replying, forwarding, deletion, filter changes, identity changes, and mailbox-setting mutations require current interactive approval; headless execution must fail closed. Show useful action details without dumping arbitrary message content.

## Success criteria (checkable)

- [ ] MCP configuration references an environment placeholder, with no literal API key in tracked configuration or launcher code
- [ ] Only the required credential is allowlisted into the MCP process and installation checks report when it is missing
- [ ] Read-only Gmail tools pass without prompts; all outbound or irreversible actions request one confirmation
- [ ] Denial and headless execution block the action, and `node scripts/verify-harness.mjs` passes

## Verification commands

`node scripts/verify-harness.mjs`

## Scoring: pass / partial / fail notes

- **pass** - credential flow is scoped and every material Gmail side effect has fail-closed approval.
- **partial** - integration works but one secret or side-effect boundary is incomplete.
- **fail** - credentials are committed/exposed, messages can send headlessly, or harness fails.

## Graders-only reference evidence

Reference solution: `git -C "C:\Neura" show 2db30d98ad32e5a9466753d566ef7b8ebfe80098` (graders only - never shown to a model).

The reference uses `${COMPOSIO_API_KEY}` in MCP JSON, refreshes a user-scoped value in the launcher, adds one Gmail guardrail extension, and tests read, denied-send, and headless-send paths.
