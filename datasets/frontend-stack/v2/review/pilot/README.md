# Frontend execution pilot: source selection

Selection reviewed 2026-09-06 by Codex. This queue preserves its original
**30 selected / zero executed** selection-time metadata. Current execution status:
[five tasks checked, zero gold](../execution-pilot/README.md), as of 2026-09-07.
All records have `training_eligible: false`. This is a work queue, not a training split.

## Selection and evidence

The original inventory contained 203 candidates. Metadata screening covered all 203;
targeted source-diff inspection narrowed the pilot to 30 bounded tasks from 30 distinct
commits: 22 from `terax-ai`, eight from `testing-ide`. Coverage is five forms, five
layout, six keyboard, seven state, six frontend contracts and one build task.
These tags describe the requested work, not demonstrated mastery or difficulty.

- [tasks.jsonl](tasks.jsonl) contains prompts, scoped paths, expected baselines,
  acceptance cases, reviewer cautions, split groups and proposed verification commands.
- [manifest.json](manifest.json) binds the queue, corrected inventory and all 100
  frozen eval task files to SHA-256 hashes.
- [eval-exclusions.json](eval-exclusions.json) preserves the 60 removed source records
  and their exact reserved-hash matches.

Each task records real full parent/reference hashes, source blob identities, full and
scoped patch hashes, and parent dependency manifest/lock hashes. Those were read from
local Git objects. No source checkout was modified. Commit messages' claimed tests,
performance savings and manual checks are not execution evidence for this pilot.

## Isolation bug repaired

The inventory parser recognized legacy `Source: ... commit ...` lines but missed V2
`Reference commit:` lines. As a result, 60 frontend candidates used a frozen eval
reference or start commit as their reference or parent. The parser now recognizes
both reference formats and expands each reference to its parent. Start lines are
not separately expanded to grandparents.

The corrected reservation set contains 195 unique hashes and matches the independent
frozen-task parser's reference/start set for all 100 tasks. Frontend inventory was
rebuilt from 203 to **143** candidates. The two new regression tests exercise both
formats and exclusion at both candidate reference and parent. The V2 validator now
shares the same reference regex.

Other specialist inventories remain unchanged historical artifacts. Rebuild them with
the repaired parser before generation; do not rely on their previous readiness status.
No V1 data, frozen eval task or archived notebook was edited.

Exact source identity exclusion is not semantic contamination clearance. Parent trees
can contain older eval-related implementations. The pilot must expose only necessary
source context and must not give the solver Git history, eval files, reference patches,
reference tests or this grader-side queue. Inspect captured reads for solution exposure
before admission. Shared paths and related task families need independent review.

The Windows tab-basename candidate was not selected because it repeats the basename
repair in a frozen code-review task. Broad native/backend work, whole-app redesigns,
provider endpoint-default repairs near backend eval coverage, and metadata-only edits
were also deferred. Deferred candidates are not classified as defective or approved.

## Execution contract

1. Choose a task and export its exact parent into a fresh isolated directory without
   Git history. Read any applicable source instructions. Keep original repositories
   and the Master-Models worktree intact.
2. Resolve Node and pnpm versions, install from the recorded parent lockfile, and
   record their exact versions and setup output. Some source manifests do not pin
   pnpm. Pin the separate Vitest/browser harness and its lockfile before execution;
   never silently update the source dependency graph. Dependency-changing tasks
   explicitly include package/lock edits in their scope.
3. Write focused acceptance fixtures against real source imports. Use recording
   Tauri/store/chat adapters with stated contracts; never imply they establish native
   shell behavior, live model-server acceptance or end-to-end backend integration.
   No local model training or live inference is needed for these checks.
4. Capture the parent failing the requested criterion before implementation. For a
   feature, this is feature absence; for styling, it is a measurable visual mismatch.
   Do not convert those into invented crash reports. An import failure alone does not
   establish the behavior of an existing component.
5. Implement only the task scope, then rerun focused checks and typechecking after the
   final edit. Browser-required tasks need real keyboard/pointer or computed-layout
   evidence. Keep unrelated failures explicit. Every command event must preserve exact
   arguments, stdout, stderr, exit status, timing and relevant file hashes.
6. Save baseline/final patches and run bundles. Review causality and complete evidence
   independently. The reference is factual grounding, not an infallible patch: notes
   call out parser edge cases, tooltip inheritance, state-updater side effects and
   dirty-editor protection that need particular care.
7. Pin the Qwen3-4B tokenizer/chat template and measure whole records at 3,072 tokens.
   Token risk labels are estimates only. Reject oversized records whole. Keep each
   source task and the broader `split_group` together when later assigning splits.

The `vitest.pilot.config.ts`, `playwright.pilot.config.ts` and per-task test paths in
the queue are **specifications for harness creation**, not existing runnable tests.
Their creation and dependency pins are the immediate execution prerequisites. Source
lockfile presence and a proposed command do not prove successful installation or tests.
The parent testing-ide Vitest configuration uses a Node environment and allows no tests;
the pilot harness must explicitly provide a DOM/browser environment where needed and
fail when its named test is absent. Terax snapshots do not supply a common test runner.

Start with tasks 15 (pane identity), 29 (pane limit), 01 (input), 10 (keyless provider)
and 20 (tooltip). This samples pure logic, hooks, forms, contracts and real rendering
before spending execution time on the larger feature tasks. Expand through all 30 only
after baseline sensitivity and honest evidence capture work.

## Verify selection metadata

```powershell
py -3 -m unittest scripts.test_v2_source_inventory scripts.test_frontend_hardening scripts.test_gate_proxy
py -3 scripts/build_v2_source_inventory.py --specialist frontend-stack --check
py -3 scripts/validate_frontend_pilot.py
py -3 scripts/validate_v2_dataset.py --specialist frontend-stack
git diff --check
```

These commands validate selection and dataset foundations; they do not execute any
pilot task. Validation remains intentionally distinct from training readiness.

Verification on 2026-09-06: all 25 regression/guard tests passed; frontend inventory
freshness passed (143); pilot metadata validation passed (30 tasks, 195 reserved
hashes); frontend foundation validation passed with zero trajectories; `git diff
--check` passed. Protected-path comparison found no tracked V1, eval, notebook or
other-domain dataset changes. Everything remains unstaged; no commit or push.

The full-registry validator now fails as expected at
`datasets/backend-stack/v2/sources/candidates.jsonl:1: overlaps a frozen eval commit`.
This exposes an existing stale inventory through the corrected admission check.
It is not a passing all-specialist foundation result.

## Selected tasks

| Task | Repository | Scope | Token-fit risk |
|---|---|---|---|
| frontend-pilot-01 | testing-ide | Compact input with visible keyboard focus | medium |
| frontend-pilot-02 | testing-ide | Theme markdown tables and code | medium |
| frontend-pilot-03 | terax-ai | Select first explorer item on focus | medium |
| frontend-pilot-04 | terax-ai | Navigate explorer search results | medium |
| frontend-pilot-05 | terax-ai | Keep keyboard selection under stationary pointer | medium |
| frontend-pilot-06 | terax-ai | Shift+Enter terminal input encoding | medium |
| frontend-pilot-07 | terax-ai | Apply zoom once and bound updates | medium |
| frontend-pilot-08 | terax-ai | Persist and apply terminal font family | high |
| frontend-pilot-09 | terax-ai | Configure compatible endpoint from settings | high |
| frontend-pilot-10 | terax-ai | Allow keyless provider selection and send | medium |
| frontend-pilot-11 | testing-ide | Validate custom generation events | medium |
| frontend-pilot-12 | testing-ide | Filter artifact review queue | medium |
| frontend-pilot-13 | testing-ide | Extract readable partial streaming text | high |
| frontend-pilot-14 | testing-ide | Render a local text diff | high |
| frontend-pilot-15 | terax-ai | Preserve unchanged pane-tree identity | low |
| frontend-pilot-16 | terax-ai | Build drive-aware breadcrumbs | medium |
| frontend-pilot-17 | terax-ai | Load Go language support lazily | low |
| frontend-pilot-18 | terax-ai | Load C-family legacy language modes | low |
| frontend-pilot-19 | terax-ai | Compact source-control header and upstream label | medium |
| frontend-pilot-20 | terax-ai | Match tooltip arrow to custom surface | medium |
| frontend-pilot-21 | terax-ai | Simplify header search placeholder | low |
| frontend-pilot-22 | terax-ai | Remove unused math rendering plugin | medium |
| frontend-pilot-23 | terax-ai | Accept known hashtag commands in composer | medium |
| frontend-pilot-24 | terax-ai | Navigate visible explorer tree by keyboard | high |
| frontend-pilot-25 | testing-ide | Open and filter command palette | high |
| frontend-pilot-26 | testing-ide | Reopen recent projects from toolbar | high |
| frontend-pilot-27 | terax-ai | Preview and pin file tabs | high |
| frontend-pilot-28 | terax-ai | Reload editor from file-written event | high |
| frontend-pilot-29 | terax-ai | Bound terminal pane count per tab | low |
| frontend-pilot-30 | terax-ai | Format AI panel shortcut hints consistently | low |
