# Task 05 - Keep delegated-agent artifacts out of version control

Source repository: `neura`
Source checkout: `C:\Neura`
Reference commit: `63a3935a334b90f3c830b1eacba9dd9b210caffc`
Start commit: `38fe32c9252ac2aa542b1a9d89d9486871601f4a`
Difficulty: **easy**

## Prompt (given to the agent verbatim)

Delegated-agent runtime artifacts are currently tracked even though they can contain user prompts, model output, local paths, metadata, and full transcripts. Remove the committed runtime artifacts and ensure future files from that runtime directory cannot enter version control. Keep source code and durable project documentation unchanged.

## Success criteria (checkable)

- [ ] No delegated-agent runtime artifact remains tracked
- [ ] The complete runtime artifact directory is ignored rather than listing individual generated filenames
- [ ] Prompts, transcripts, output, metadata, and future run identifiers are covered by the ignore boundary
- [ ] Source code, settings, and durable documentation are unchanged

## Verification commands

```powershell
$tracked = @(git ls-files -- '.pi-subagents/**')
if ($tracked.Count -ne 0) { throw "delegated-agent artifacts remain tracked: $($tracked -join ', ')" }
$probe = '.pi-subagents/artifacts/security-eval-transcript.jsonl'
$ignored = git check-ignore --no-index -- $probe
if ($LASTEXITCODE -ne 0 -or $ignored -ne $probe) { throw 'runtime artifact directory is not fully ignored' }
$changed = @(git status --porcelain=v1 --untracked-files=all | ForEach-Object { $_.Substring(3) })
if (@($changed | Where-Object { $_ -ne '.gitignore' -and $_ -notlike '.pi-subagents/*' }).Count -ne 0) { throw 'unrelated files changed' }
```

## Scoring: pass / partial / fail notes

- **pass** - tracked runtime records are removed and one directory-level ignore rule prevents future prompt/transcript disclosure.
- **partial** - current artifacts are removed but the ignore boundary is incomplete or overly broad.
- **fail** - generated prompts or transcripts remain tracked, only known filenames are ignored, or unrelated durable files change.

## Graders-only reference evidence

Reference solution: `git -C "C:\Neura" show 63a3935a334b90f3c830b1eacba9dd9b210caffc` (graders only - never shown to a model).

The reference removes four tracked `.pi-subagents/artifacts` records and adds one `.pi-subagents/` rule to `.gitignore`. At the start object, `git ls-tree -r --name-only 38fe32c9252ac2aa542b1a9d89d9486871601f4a -- .pi-subagents` returns those records; at the reference object it returns none.
