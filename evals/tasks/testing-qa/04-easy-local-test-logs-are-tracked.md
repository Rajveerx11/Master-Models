# Task 04 - Local test logs are tracked

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `aacd91e6c3f2ee77026367767b0a754bc6141ba7`
Start commit: `7ba5dfdffaf8157e5b430a104005b7fdeff55373`
Difficulty: **easy**
Category: test-output hygiene

## Prompt (given to the agent verbatim)

A captured Clippy output file was accidentally committed under the desktop Rust tree. Remove that generated artifact from version control and prevent both Clippy and test scratch logs in the same location from being committed again. Do not ignore source files, lockfiles, or general application logs.

## Success criteria (checkable)

- [ ] The tracked Clippy scratch output is removed.
- [ ] Desktop ignore rules cover both local Clippy and test scratch logs under `src-tauri`.
- [ ] Ignore patterns stay narrow and do not hide arbitrary logs elsewhere.
- [ ] No source or dependency files change.

## Verification commands

```powershell
git ls-files apps/desktop/src-tauri/clippy.log apps/desktop/src-tauri/test.log
git check-ignore apps/desktop/src-tauri/clippy.log apps/desktop/src-tauri/test.log
```

## Scoring: pass / partial / fail notes

- **pass** - tracked scratch output is gone and both narrow ignore rules work.
- **partial** - current file is removed but future Clippy/test output is only partly protected.
- **fail** - generated output remains tracked, ignore scope is broad, or source/dependency files change.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 7ba5dfdffaf8157e5b430a104005b7fdeff55373 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference deletes `apps/desktop/src-tauri/clippy.log` and adds only `src-tauri/clippy.log` plus `src-tauri/test.log` to `apps/desktop/.gitignore`. Inspect with `git -C "C:\Testing IDE" show aacd91e6c3f2ee77026367767b0a754bc6141ba7`.
