# Task 10 - Reverse patch restores unrestricted filesystem capability

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `9c6ca4ef32c7ff953e843369e51ac8b231fbed6f`
Start commit: `ef85a84f2cdcb7a38cdb933fd23d6ed18918becf`
Difficulty: **medium**
Task mode: **review**
Patch files: `apps/desktop/src-tauri/capabilities/default.json`, `apps/desktop/src/components/file-explorer/file-explorer.tsx`, `apps/desktop/src/lib/ipc/filesystem.ts`
Patch base: `9c6ca4ef32c7ff953e843369e51ac8b231fbed6f`
Patch target: `ef85a84f2cdcb7a38cdb933fd23d6ed18918becf`
Patch direction: **defective-reverse**

## Prompt (given to the agent verbatim)

Review the supplied patch in repository context. Report only concrete defects introduced by this patch that can cause incorrect behavior, broken contracts, data loss, security problems, or meaningful reliability regressions. For each finding, cite the exact file and changed lines, explain the trigger and impact, and propose the smallest correction. Do not report style preferences or pre-existing issues. If no actionable defect exists, return no findings.

## Success criteria (checkable)

- [ ] Review identifies that the restored `**` and `**/*` capability scopes bypass the intended home/documents/desktop/download allowlist
- [ ] Finding explains that the desktop frontend can again access arbitrary filesystem paths through the plugin rather than only approved user locations
- [ ] Review cites the capability change and proposes removing the global wildcards while avoiding false findings about the type-only frontend changes

## Verification commands

`pnpm --filter @testing-ide/desktop typecheck && pnpm --filter @testing-ide/desktop test`

## Scoring: pass / partial / fail notes

- **pass** - reaches the graders-only expected outcome with precise changed-line evidence, correct impact, and no false positives.
- **partial** - notices the broadened capability but gives incomplete scope, impact, or remediation analysis.
- **fail** - misses the proven defect, reports only style, or reviews pre-existing code.

## Graders-only reference evidence

Expected outcome: **finding expected**.

Reference solution: `git -C "C:\Testing IDE" show 9c6ca4ef32c7ff953e843369e51ac8b231fbed6f` (graders only - never shown to a model).

The reverse patch adds global `**` and `**/*` filesystem permission scopes alongside the explicit user-directory allowlist. Those wildcards make the restriction ineffective and re-enable reads outside the intended locations; the other changes are type/lint-only.
