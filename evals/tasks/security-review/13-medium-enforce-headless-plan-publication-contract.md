# Task 13 - Enforce headless Plan publication contract

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `ce1ef4b62a774ce1ab723b0ae286e3a6993788b3`
Start commit: `c138abb4982208c2de5901621e16819252660ec1`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Plan mode currently enforces artifact publication only through an interactive UI settlement path. Extend the contract to TUI, print, JSON, and RPC inputs. Queue at most one retry only after a completed assistant turn, preserve deliberate waits and provider recovery, and persist one machine-readable terminal outcome so restarts cannot duplicate retry or failure state.

## Success criteria (checkable)

- [ ] All non-extension input sources start or resume the same publication lifecycle
- [ ] Only a normally completed assistant run consumes the single publication retry
- [ ] Waiting, aborted, failed-provider, and successfully published paths do not receive stale retries
- [ ] Published and terminal-failure outcomes are versioned, persisted, restart-safe, and covered by harness tests

## Verification commands

`node scripts/verify-harness.mjs`

## Scoring: pass / partial / fail notes

- **pass** - headless and UI flows share a bounded, durable, continuation-safe contract.
- **partial** - headless enforcement works but retries or persisted terminal states have lifecycle gaps.
- **fail** - requests can bypass publication, loop retries, duplicate failures, or harness fails.

## Graders-only reference evidence

Reference solution: `git -C "C:\Neura" show ce1ef4b62a774ce1ab723b0ae286e3a6993788b3` (graders only - never shown to a model).

The reference moves retry decisions to completed `agent_end` events, records versioned contract entries, and adds headless, RPC, recovery, restart, wait, failure, and publication tests.
