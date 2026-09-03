# Task 14 - Clean Rust-optional pre-push hook repair

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `3b4b54b7668ec4df1af612952873536c6730e675`
Start commit: `0892168b536498e77a8a1088a40e138b21ce0938`
Difficulty: **medium**
Task mode: **review**
Patch files: `CONTRIBUTING.md`, `README.md`, `docs/AGENT_WORKFLOW.md`, `tools/scripts/pre-push.sh`
Patch base: `0892168b536498e77a8a1088a40e138b21ce0938`
Patch target: `3b4b54b7668ec4df1af612952873536c6730e675`
Patch direction: **clean-forward**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review verifies that shared and desktop frontend tests still run unconditionally before push
- [ ] Review verifies that Rust Clippy and unit tests run when Cargo is available and remain enforced in CI
- [ ] Review confirms the contributor documentation matches the hook behavior and returns no actionable findings

## Verification commands

`bash -n tools/scripts/pre-push.sh && pnpm --filter @testing-ide/shared run test && pnpm --filter @testing-ide/desktop run test:frontend`

## Scoring: pass / partial / fail notes

- **pass** - returns no findings after checking the hook's conditional boundary, retained test coverage, and matching documentation.
- **partial** - raises an unsupported concern without asserting a concrete introduced defect.
- **fail** - invents an actionable regression, reports style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **no findings**.

Reference solution: `git -C "C:\Testing IDE" show 3b4b54b7668ec4df1af612952873536c6730e675` (graders only - never shown to a model).

The forward patch replaces the root test command with explicit shared and desktop frontend suites, leaving Rust Clippy and unit tests behind the existing Cargo-availability guard. CI still requires Rust, and all three documentation files accurately describe that local/CI boundary.
