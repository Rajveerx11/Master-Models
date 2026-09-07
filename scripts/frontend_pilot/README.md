# Frontend execution harness

This harness imports real source files from isolated parent archives. It is not a
native application test suite or a training launcher. Package versions and pnpm
integrities are pinned in `package.json` and `pnpm-lock.yaml`. React and TypeScript
resolve from each source snapshot; the harness owns Vitest, jsdom and Playwright.

Node `v24.16.0`, pnpm `10.9.0`, Git Bash and Python are required. Browser checks use
Playwright `1.62.0` with Chromium revision `1234` (`151.0.7922.34`). The browser
script is copied to OS TEMP and run through the local playwright-skill entry point.
Vite serves only the isolated fixtures and closes in `finally`.

On a fresh output directory:

```powershell
py -3 scripts/run_frontend_pilot.py prepare 1 10 15 20 29
py -3 scripts/run_frontend_pilot.py repair-setup 1
py -3 scripts/run_frontend_pilot.py configure
node outputs/frontend-pilot/harness/node_modules/@playwright/test/cli.js install chromium
py -3 scripts/run_frontend_pilot.py tool 15 outputs/frontend-pilot/check-call.json
py -3 scripts/run_frontend_pilot.py tool 29 outputs/frontend-pilot/check-call.json
py -3 scripts/run_frontend_pilot.py tool 10 outputs/frontend-pilot/check-call.json
py -3 scripts/run_frontend_pilot.py tool 1 outputs/frontend-pilot/browser-call.json
py -3 scripts/run_frontend_pilot.py tool 10 outputs/frontend-pilot/browser-call.json
py -3 scripts/run_frontend_pilot.py tool 20 outputs/frontend-pilot/browser-call.json
```

These parent checks should fail on the requested criteria. Missing dependencies,
empty test suites, runtime errors and fixture mistakes are infrastructure failures,
not evidence of the task defect. `prepare` refuses to overwrite existing snapshots.
The existing output directory contains preserved evidence; do not reset it to run
this example. Use a separate checkout/output root for another attempt.

After reading the relevant source through `tool ... read-call.json`, the two
`apply_*_fixes.py` modules apply the recorded exact-string edits. They refuse
nonunique matches and are not idempotent. Rerun each applicable focused/browser check
after the last edit. Run `typecheck-call.json` for terax tasks and
`typecheck-desktop-call.json` for task 01. Both invoke the source-pinned compiler
directly, avoiding the observed pnpm/Git-Bash command-shell problem.

Task 01 has a hash-guarded setup overlay: its root manifest lists husky while its
lockfile does not. Only that Git-hook dev dependency is removed; the source lockfile
is preserved. `setup-overlay.json` records the exact before/after hashes.

The task-10 unit suite mocks the Chat SDK boundary to record send calls. Browser
fixtures stub composer, platform and settings-window boundaries. They do not prove
native Tauri behavior, a network request or live model inference. Task 20 tests solid
surface colors in Chromium; other browsers, gradients and edge collisions remain
outside this fixture's coverage.

For complete-record measurement, create an isolated Python environment and install
`requirements-tokenizer.lock.txt`. Download only the tokenizer files at the revision
in `training/templates/qwen3-4b.pin.json` into `outputs/frontend-pilot/tokenizer`.
Then run `scripts/measure_frontend_pilot.py` with that environment and
`scripts/export_frontend_pilot.py` with Python. Export validates archived source,
scoped changes and every captured edit's hash chain. Use
`scripts/validate_frontend_execution.py` to check the portable evidence bundle.

Never remove failed events to meet the token cap. New compact episodes require fresh
execution with a preflighted harness and deliberately focused reads. The historical
oversized episodes stay intact and training-ineligible.
