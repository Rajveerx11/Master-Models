# Task 09 - Verify edits with a bounded proof gate

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `c53f7ac1c5d0338c71b10182fcfefd97633ffc29`
Start commit: `20f5330ad777092daa0c046ba5ce993829eb3a3e`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Add a Neura-only verification gate that detects whether an agent turn changed the Git worktree, runs a quick proof-of-work check after changed turns, and feeds one failed verdict back for repair. It must never enter an automatic retry loop, block plain Pi, or crash when Git, the verifier, JSON output, or the interactive session is unavailable. Also provide an explicit command for the full test-backed shipping check.

## Success criteria (checkable)

- [ ] The extension is inactive outside Neura sessions
- [ ] Worktree fingerprints detect edits from file and shell tools
- [ ] Quick verification runs only after changed interactive work in a Git repository
- [ ] A failed quick verdict creates at most one repair follow-up per user prompt
- [ ] Missing tools, invalid JSON, concurrent checks, and replaced sessions fail softly
- [ ] The shipping command runs the full verifier with a bounded timeout and reports pass/fail actionably
- [ ] TypeScript checking passes

## Verification commands

```powershell
npx tsc --noEmit
```

## Scoring: pass / partial / fail notes

- **pass** - change detection, bounded quick feedback, full shipping verification, isolation, and failure handling all work.
- **partial** - verification works but retries, concurrency, non-Git behavior, or failures are not safely bounded.
- **fail** - unchanged turns trigger work, feedback loops indefinitely, plain Pi changes, or checks fail.

## Graders-only reference evidence

Run this extension-contract discriminator:

```powershell
$path = 'agent/extensions/check-gate.ts'
if (-not (Test-Path $path)) { exit 1 }
$source = Get-Content $path -Raw
foreach ($marker in @('proof-of-work', '--no-tests', 'let fedBack = false', 'let checking = false', '90_000', '600_000', 'registerCommand("ship"')) { if (-not $source.Contains($marker)) { exit 1 } }
```

The extension file does not exist at `20f5330ad777092daa0c046ba5ce993829eb3a3e`; every bounded quick/full and one-feedback marker exists at `c53f7ac1c5d0338c71b10182fcfefd97633ffc29`.

The reference adds `agent/extensions/check-gate.ts` with Git status/diff fingerprints, quick/full proof-of-work execution, one-feedback state, concurrency guard, timeouts, and `/ship`. Inspect with `git diff 20f5330ad777092daa0c046ba5ce993829eb3a3e c53f7ac1c5d0338c71b10182fcfefd97633ffc29 -- agent/extensions/check-gate.ts`.
