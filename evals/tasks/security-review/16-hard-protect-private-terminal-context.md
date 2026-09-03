# Task 16 - Protect private terminal context

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `7db88b374c598937bd3c54e0d4fcd32bee4df3c7`
Start commit: `83cc3049087cba16e5bf0394090478044d49fac3`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Users need a terminal tab for commands whose output must never be copied into AI context. Add a clearly identifiable private-terminal mode across tab creation, UI state, status indicators, shortcuts, and context transport. For normal terminals, redact common credential formats and secret assignments before transport. Privacy must follow the tab itself and default closed whenever state is absent.

## Success criteria (checkable)

- [ ] Users can create and identify a private terminal through the existing tab UI and shortcut system
- [ ] Private state is stored on the terminal tab and the active tab determines current privacy state
- [ ] Private terminal output is never inserted into AI context; the context states that it was intentionally withheld
- [ ] Normal terminal context redacts major provider tokens, JWTs, bearer tokens, and secret-like assignments
- [ ] Existing tabs default non-private and frontend typecheck/tests pass

## Verification commands

`pnpm exec tsc --noEmit && pnpm test`

## Scoring: pass / partial / fail notes

- **pass** - privacy propagates end to end and normal context is redacted without exposing matched values.
- **partial** - output is hidden in one path but tab lifecycle, UI, reconnect, or redaction coverage is incomplete.
- **fail** - private output reaches the model, privacy leaks across tabs, secrets remain visible, or checks fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\terax-ai" show 7db88b374c598937bd3c54e0d4fcd32bee4df3c7` (graders only - never shown to a model).

The reference adds tab-level private state, creation/UI plumbing, status presentation, a central redactor, and transport logic that substitutes an explicit withheld-output block.
