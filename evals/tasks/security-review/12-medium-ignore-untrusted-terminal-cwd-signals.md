# Task 12 - Ignore untrusted terminal CWD signals

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `32a5ec97da8143c664c03ea67d155ebf988024e6`
Start commit: `10aacd39b12f16e4d887c35c189a2245c02e77d5`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Terminal output can emit a working-directory control sequence. Remote sessions or attacker-controlled output can therefore relocate the application's relative-path base while a command runs. Use shell command-boundary signals to accept local prompt-time directory updates but ignore directory reports produced inside a running command. Preserve existing parsing for callers that do not opt into state tracking.

## Success criteria (checkable)

- [ ] Command-start and pre-exec markers enter an in-command state; exit and next-prompt markers clear it
- [ ] Working-directory reports are ignored during that state and accepted between commands
- [ ] State is scoped to each terminal session and reset safely on lifecycle changes
- [ ] Legacy stateless parsing remains compatible and focused terminal tests pass

## Verification commands

`pnpm test -- src/modules/terminal/lib/osc-handlers.test.ts`

## Scoring: pass / partial / fail notes

- **pass** - untrusted in-command directory reports cannot change application state; prompt updates still work.
- **partial** - gating exists but state transitions, reset, or compatibility is incomplete.
- **fail** - command output can still redirect relative paths or legitimate updates break.

## Graders-only reference evidence

Reference solution: `git -C "C:\terax-ai" show 32a5ec97da8143c664c03ea67d155ebf988024e6` (graders only - never shown to a model).

The reference tracks OSC 133 B/C/D/A state in `osc-handlers.ts`, passes it from the terminal session hook, and adds five gated/ungated tests.
