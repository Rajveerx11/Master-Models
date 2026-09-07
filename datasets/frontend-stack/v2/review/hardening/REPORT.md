# Frontend dataset hardening report

Checked: 2026-09-06. Reviewer: Codex.

## Decision

Do not train the existing V1 mix. The audit found concrete code/trace defects,
incorrect teaching explanations, invalid tool-schema examples, and a corpus-wide
absence of captured execution provenance. A believable transcript is not an
execution record.

This work completed whole-corpus static screening, targeted semantic inspection,
quarantine, four explanation repairs, and stronger admission checks. It did **not**
complete independent semantic approval or actual project execution for every record.
No frontend example is promoted to V2 gold by this report.

## Scope and results

| Evidence | Result |
|---|---|
| Canonical raw frontend batches | All 350 screened; raw part copies reconciled |
| Seeds | Both inspected structurally; one is an empty placeholder |
| Retained frontend corpus | All 242 screened, including scores 8 and 9 |
| V1 final mix | All 384 train + 20 holdout records checked |
| V1 bounded derivatives | All 328 train + 18 holdout checked; unchanged subsets |
| Reconstructed code | 675 full JS/TS snapshots statically checked with TypeScript 5.9.3 |
| Frontend quarantine | 5 retained examples excluded from replay candidates |
| Frontend candidates | 237 retained examples require real replay/rebuilding |
| Summary corrections | 4, applied only to separate candidate copies |
| General/tool quarantine | 3 Hermes examples; 7 argument/schema violations |
| General candidates | 159 schema-checked examples, preserving original split labels |
| V2 gold approved | 0 |

Original V1 datasets, frozen eval tasks, and the archived notebook are unchanged.
The legacy score-7 queue remains historical/pending; it is not silently marked as
human-approved. The new ledger covers all scores and supersedes it for triage.

## Confirmed defects and corrections

`keep line` refers to `datasets/frontend-stack/filtered/keep_ge7.pi.jsonl`.

| Keep line | Source ID / score | Action | Evidence |
|---|---|---|---|
| 127 | batch4:44 / 7 | Quarantine | Edit removes an opening wrapper but leaves its closing `div`; reconstructed JSX fails parsing despite recorded clean tsc |
| 137 | batch4:57 / 8 | Quarantine | Exact edit target occurs twice; pi requires a unique target, but the result claims one replacement |
| 42 | batch3:25 / 7 | Quarantine | NavLink active state is derived from current props/location; shown code does not establish the claimed stale active styling caused by index-key reuse |
| 50 | batch3:33 / 7 | Quarantine | Insertion with index keys reuses positions; explanation incorrectly claims every following element remounts; no animation reproduction shown |
| 89 | batch3:78 / 9 | Quarantine | Tuesday is `getDay() === 2`, so Monday-first array index `2 - 1` is Tuesday; task and explanation incorrectly claim Monday |
| 45 | batch3:28 / 8 | Correct summary, replay required | `transition-property: transform` does not itself apply a transform; remove invented containing-block and measured-height claims |
| 131 | batch4:49 / 8 | Correct summary, replay required | HTML class order does not determine CSS cascade; confirm unseen `cn` helper implements merging |
| 152 | batch4:74 / 9 | Correct summary, replay required | Relational comparison uses numeric primitive conversion; ISO string becomes NaN, not lexicographic comparison with Date.toString |
| 171 | batch4:96 / 8 | Correct summary, replay required | Attribute presence explains the CSS bug; `aria-current=false` does not mark an item current to assistive technology |

The three invalid general/tool records are V1 `train.jsonl` lines 236, 278 and 357.
Their schemas include contradictions such as a string parameter restricted to
`enum: [null]`, while their calls supply strings or null. They also survive into
the 4,096-token derivative. They were excluded rather than silently guessing a
replacement tool contract.

## Corpus-wide evidence problem

The V1 teacher prompt requests realistic tool results. Its records contain no
immutable source identity or captured execution bundle. All 1,451 tool-result
messages in the retained set lack exit-code metadata. Adding zero exit codes now
would fabricate evidence, not repair the dataset.

Source and execution gaps apply to all 242 records, including apparently correct
ones. The 237 candidates are reusable *task ideas and provisional traces*, not
verified examples. The four corrected summaries explicitly refer to recorded
output rather than claiming a new successful run. No tool output was changed.

Additional review flags overlap:

- 8 records edit context shown only in search/compiler fragments.
- 6 contain partial or refused file reads.
- 4 overwrite a file with prior existence evidence without reading its content.
- 3 depend on ambient test/Node identifiers not resolvable from the snapshots.
- 8 contain React-version-sensitive unmounted-state warning explanations.
- 17 mention browser/visual interaction in summaries and need claim-scope review.
- 1 leaves a failing test and explicitly discloses it. This honesty is preserved;
  a real baseline and a separate focused successful check are still needed.

These flags are **review signals**, not automatic findings of defective code.
TypeScript checks do not resolve the original dependency graph, run a full project
typecheck, execute tests, or verify browser behavior. Removed files and mutations
inside arbitrary shell commands are not replayed. Such commands are never executed
by this auditor.

## Isolation and coverage

Raw-to-retained identity and pi conversion agree. The final mix preserves all
retained domain exchanges. The short derivatives contain unchanged records from
their corresponding original splits. There are no exact retained prompt/trace
duplicates or normalized train/holdout prompt overlaps.

All 100 frozen eval prompts were scanned against raw/seed prompts. No pair met the
configured lexical overlap threshold (Jaccard >= 0.45, at least 12 common tokens).
No retained prompt pair met the internal review threshold (0.50, 12 common tokens).
These are lexical screens, **not clearance of semantic paraphrases or reference
patch contamination**. Missing V1 source identity prevents strong source isolation.

Overlapping lexical coverage tags across retained records:

| Tag | Records |
|---|---:|
| Layout/responsive | 178 |
| Accessibility/keyboard | 150 |
| Forms/validation | 133 |
| State/async/lifecycle | 101 |
| Data/persistence | 90 |
| Routing | 37 |

These counts reflect mentions, not difficulty, mastery, or test adequacy. The corpus
contains many useful small React repairs, but this is not proof of broad frontend
engineering ability. Actual regression tests, keyboard/browser checks, multi-file
contracts and unfamiliar repositories should determine the rebuilt coverage mix.
The Qwen3-4B 3,072-token fit has not yet been measured.

## Changes delivered

- `audit.jsonl`: one traceable decision for each raw/seed record, source hash,
  retained index/score, findings, commands and coverage tags.
- `quarantine.jsonl`: five excluded retained examples and reasons.
- `replay-candidates.jsonl`: 237 complete pi-format candidates with explicit
  `training_eligible: false`; four corrected summaries, original tool traces.
- `replay-queue.jsonl`: compact pointers and outstanding checks.
- `general-quarantine.jsonl` / `general-candidates.jsonl`: three excluded examples
  and 159 schema-checked general examples with original split labels.
- `semantic-decisions.json`: source-hash-bound corrections and reasons.
- `typescript-diagnostics.json`: reproducible static diagnostics, not test results.
- `manifest.json`: input/output hashes, counts, duplicate checks and limitations.
- `scripts/validate_v2_dataset.py`: real source ancestry/path checks, full tool
  argument schema validation, integer exit-code requirements, rejection of explicit
  failed verification paired with zero exit status, post-edit verification,
  review/score requirements for final rows, exact eval-prompt checks and source-task
  train/holdout separation.

V2 validation remains an admission check for domain trajectories. It does not prove
that supplied metadata was captured honestly. The future training-mix packer must
separately validate general examples against their own schemas, rather than force
them into the source-grounded domain schema.

## Next checkpoint

1. Review non-eval frontend source candidates and select **30 real tasks** spanning
   async/state, forms, keyboard/accessibility, layout and multi-file contracts.
   Use old candidates for coverage ideas; do not attach invented Git provenance.
2. Rebuild trajectories in isolated repository snapshots. Capture exact reads,
   edits, stdout/stderr and exit codes with repository/dependency revisions and
   hashes. Confirm the reported bug before its fix. Keep eval reference material
   out of the agent workspace.
3. Run focused tests and typechecks; use browser checks for visual/keyboard claims.
   Keep accurate failure disclosures. Reject causality invented around a plausible
   patch. Record independent semantic review separately from judge scores.
4. Pin the 4B tokenizer/template and measure whole-record token fit on this pilot.
   Reject oversized records whole; do not truncate tool exchanges.
5. If the pilot meets quality and length requirements, expand toward 180-220 gold
   domain trajectories, group source tasks before train/holdout splitting, add the
   reviewed general mix, and freeze manifests. Then build the Colab notebook and
   compare trained versus stock 4B on the existing frontend gate.

The next useful investment is **a small, actually executed frontend corpus**.
Training the old mix now would confound model quality with known dataset defects.

## Reproduce and verify

Raw batches are local, gitignored inputs. Their hashes are recorded in the manifest;
the audit fails if those inputs are unavailable. Committed retained data alone is
not enough to reproduce the all-raw audit. A shareable release will need those
inputs or a separate distributable source-grounded corpus.

```powershell
py -3 -m pip install -r scripts/requirements-audit.txt
npm install --prefix outputs/frontend-audit/tooling --ignore-scripts --no-audit --no-fund typescript@5.9.3
py -3 scripts/audit_frontend_dataset.py --snapshots outputs/frontend-audit/snapshots.json
node scripts/check_frontend_snapshots.cjs outputs/frontend-audit/tooling/node_modules/typescript outputs/frontend-audit/snapshots.json datasets/frontend-stack/v2/review/hardening/typescript-diagnostics.json
py -3 scripts/audit_frontend_dataset.py --check
py -3 -m unittest scripts.test_frontend_hardening scripts.test_gate_proxy
py -3 scripts/validate_eval_tasks.py --require-v2
py -3 scripts/validate_v2_dataset.py --registry datasets/v2-registry.json
```

Use the audit command without `--check` only to regenerate audit outputs. Dataset
validation still reports zero V2 trajectories; a passing foundation check is not a
training release. Strict frontend validation must fail until final V2 splits exist.

Verification on 2026-09-06: deterministic audit check passed; 23 regression/guard
tests passed; V1 mix demo and legacy review-queue checks passed; V2 foundation
validation passed with zero trajectories. Strict frontend admission failed as
expected with `frontend-stack: no V2 trajectory files`.
All 100 frozen eval tasks validated. Candidate-copy comparison confirmed that all
tool exchanges remain unchanged and exactly four final summaries differ from V1.

## Technical references for semantic corrections

- [React list identity](https://react.dev/learn/rendering-lists)
- [NavLink active state](https://reactrouter.com/api/components/NavLink)
- [CSS transition-property](https://www.w3.org/TR/css-transitions-1/#transition-property-property)
- [Tailwind conflicting utilities](https://tailwindcss.com/docs/styling-with-utility-classes#conflicting-utility-classes)
- [ECMAScript relational comparison](https://tc39.es/ecma262/multipage/abstract-operations.html#sec-islessthan)
- [WAI-ARIA current state](https://www.w3.org/TR/wai-aria-1.2/#aria-current)
