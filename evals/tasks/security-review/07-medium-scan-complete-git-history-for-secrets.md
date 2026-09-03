# Task 07 - Scan complete Git history for secrets

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `287f30dbd0e6f0043b724c4f9b0c3618afd8b531`
Start commit: `9136e767c6e9b01c177bb704fe9d3feae79f3603`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

Current verification can miss a credential deleted from the latest tree but still present in Git history. Add a deterministic Windows-compatible secret scan covering every reachable ref. Pin the scanner and verify its downloaded archive before execution, redact findings, distinguish leak findings from tool failures, test clean, tampered-download, and committed-secret paths, and wire it into CI with full history available.

## Success criteria (checkable)

- [ ] CI checks out complete history without persisting credentials before scanning all refs
- [ ] Scanner version and archive SHA-256 are pinned and verified before extraction
- [ ] Findings are redacted; leak exit status and scanner failure status produce different failures
- [ ] Automated tests prove clean history passes while tampered tools and committed synthetic secrets fail

## Verification commands

`powershell -NoProfile -File .\scripts\verify-secrets.tests.ps1`

## Scoring: pass / partial / fail notes

- **pass** - complete-history scan is supply-chain pinned, fail-closed, redacted, tested, and in CI.
- **partial** - history scanning works but integrity, error handling, or a failure-path test is missing.
- **fail** - only working tree is scanned, unverified code runs, secrets print, or tests fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\Neura" show 287f30dbd0e6f0043b724c4f9b0c3618afd8b531` (graders only - never shown to a model).

The reference adds two PowerShell scripts and CI steps. Its tests create temporary Git repositories and exercise clean, archive-tamper, and historical-leak outcomes.
