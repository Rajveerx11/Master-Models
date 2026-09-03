# Task 13 - Healing reports the wrong final attempt

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `be3ae819634cdc2a19742041f0468a0086dddb03`
Start commit: `5a990d3ce43702715d264092c04b4242e708a109`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

The self-healing result can point at a failed sandbox run and the UI can derive failure rows from a later regressed attempt instead of the artifact that was actually retained. Keep cancelled or errored runs out of best-attempt selection. Build the displayed failure trail from the retained artifact's attempt and ignore discarded attempts that came after it.

## Success criteria (checkable)

- [ ] Cancelled and errored runs cannot become the final run
- [ ] A result with no eligible run leaves its final run identifier empty
- [ ] The UI finds the attempt associated with the retained artifact
- [ ] Failures from later discarded attempts are not shown or labelled as bugs in the retained artifact
- [ ] Existing successful, exhausted, and no-progress behavior remains intact
- [ ] Focused Rust and frontend regression tests pass

## Verification commands

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib healing_service
pnpm --filter @testing-ide/desktop exec vitest run src/components/ai-panel/sandbox-run-panel.test.tsx -t "landed"
```

## Scoring: pass / partial / fail notes

- **pass** - backend final-run selection and frontend failure rows both follow the retained successful/best attempt.
- **partial** - one layer is corrected but the other can still report a discarded or failed attempt.
- **fail** - errored runs remain eligible, regressed failures remain visible, or tests fail.

## Graders-only reference evidence

The reference considers a run only after error/cancellation exits, finds the final UI attempt by retained artifact ID, bounds later trail entries, and adds Rust plus React regressions. Inspect with `git diff 5a990d3ce43702715d264092c04b4242e708a109 be3ae819634cdc2a19742041f0468a0086dddb03 -- apps/desktop/src-tauri/src/services/healing_service.rs apps/desktop/src/components/ai-panel/sandbox-run-panel.tsx apps/desktop/src/components/ai-panel/sandbox-run-panel.test.tsx`.
