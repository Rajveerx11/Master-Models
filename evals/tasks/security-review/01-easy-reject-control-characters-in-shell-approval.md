# Task 01 - Reject control characters in shell approval

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `b7ba0eee39e4823992b7a1ba60efd764164f62b0`
Start commit: `bc205ec210b0c2389cff7e7cd872de541e134f74`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

The shell-command safety check treats an approved command as one visible line, but embedded control characters can make execution differ from what the approval UI displayed. Harden this boundary so commands containing line breaks or other C0 controls are refused, while ordinary single-line commands keep their existing behavior. Add regression coverage for representative control characters and a second-command smuggling case.

## Success criteria (checkable)

- [ ] Commands containing LF, CR, CRLF, tab, NUL, or vertical tab are rejected
- [ ] A command with a harmless first line followed by a second sensitive command is rejected
- [ ] Empty-command, bidi-character, and ordinary single-line handling remain intact
- [ ] `pnpm test -- src/modules/ai/lib/security.test.ts` passes

## Verification commands

`pnpm test -- src/modules/ai/lib/security.test.ts`

## Scoring: pass / partial / fail notes

- **pass** - every C0-control case is rejected with focused tests and no safety regression.
- **partial** - newline injection is blocked but coverage or another listed control is missed.
- **fail** - injected commands remain accepted, normal commands break, or tests fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\terax-ai" show b7ba0eee39e4823992b7a1ba60efd764164f62b0` (graders only - never shown to a model).

The reference replaces the NUL-only check in `src/modules/ai/lib/security.ts` with one C0 range guard and adds focused cases in `security.test.ts`.
