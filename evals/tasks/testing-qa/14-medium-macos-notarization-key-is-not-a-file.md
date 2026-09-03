# Task 14 - macOS notarization key is not a file

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `a3069de9987128ca9fe5f3e8c7bb4f5384858c86`
Start commit: `1e2b1c44e28ce77f3e8d823fe3fdfb034cc45fc8`
Difficulty: **medium**
Category: release-workflow repair

## Prompt (given to the agent verbatim)

macOS release notarization receives the private API key contents through a repository secret, but the signing tool expects a filesystem path. Materialize the secret only on macOS runners and pass the resulting path to subsequent steps without exposing the key or changing non-macOS jobs.

## Success criteria (checkable)

- [ ] Key material is written only on macOS matrix entries.
- [ ] The destination directory is created before writing.
- [ ] Secret content is passed through an environment variable, not interpolated into shell source or logs.
- [ ] The generated path is exported through the runner environment for the signing action.
- [ ] Linux and Windows release behavior is unchanged.
- [ ] Obsolete notarization fallback variables are not left ambiguously wired.

## Verification commands

```powershell
$workflow = Get-Content .github/workflows/release.yml -Raw
$step = [regex]::Match($workflow, "(?ms)- name:\s*Write Apple API key to disk\s*\r?\n(?<body>.*?)(?=\r?\n\s*- (?:name:|uses:))")
if (-not $step.Success) { throw 'missing Apple API key materialization step' }
$body = $step.Groups['body'].Value
foreach ($required in @("if: startsWith(matrix.platform, 'macos')", 'shell: bash', 'KEY_CONTENT:', 'mkdir -p "$HOME/private_keys"', 'printf ''%s'' "$KEY_CONTENT"', 'GITHUB_ENV')) { if ($body -notmatch [regex]::Escape($required)) { throw "Apple key step missing: $required" } }
if (([regex]::Matches($workflow, 'secrets\.APPLE_API_KEY_PATH')).Count -ne 1 -or $workflow -match '(?m)^\s+APPLE_API_KEY_PATH:\s*\$\{\{ secrets\.') { throw 'raw key contents are still wired as a path' }
if ($workflow -match '(?m)^\s+APPLE_(?:ID|PASSWORD):') { throw 'obsolete notarization fallback remains' }
pnpm build
```

## Scoring: pass / partial / fail notes

- **pass** - notarization receives a real protected file path with correct matrix scoping and no secret exposure.
- **partial** - path works but scoping, quoting, or stale environment wiring is unsafe.
- **fail** - secret is printed/interpolated, all platforms write it, or signing still receives raw contents as a path.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 1e2b1c44e28ce77f3e8d823fe3fdfb034cc45fc8 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference adds a macOS-only Bash step in `.github/workflows/release.yml`, writes the environment-provided contents with `printf`, exports `APPLE_API_KEY_PATH` through `GITHUB_ENV`, and removes stale fallback variables. Inspect with `git -C "C:\terax-ai" show a3069de9987128ca9fe5f3e8c7bb4f5384858c86`.
