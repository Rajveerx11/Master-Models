# Task 15 - Build a cross-platform PR and release gate

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `4dc87cf9f16e57d35452aa857973bb68d49fb810`
Start commit: `a9bf5700564ee412ab21b16b504d3eaba6199b41`
Difficulty: **hard**
Category: CI/release architecture

## Prompt (given to the agent verbatim)

The repository needs a complete quality and release baseline. Add pull-request gates for frontend type/build checks and Rust check/Clippy, then expand release packaging across Linux, Windows, and both macOS architectures with signing/notarization inputs. Keep platform-only setup scoped correctly, dependency updates grouped, and release outputs draft-first.

## Success criteria (checkable)

- [ ] Pushes and pull requests to the main branch run cancellable frontend and Rust gates.
- [ ] Frontend installs from the frozen lockfile, typechecks, and builds.
- [ ] Rust runs locked all-target checks and denies Clippy warnings with required Linux libraries installed.
- [ ] Release matrix covers Linux, Windows, macOS arm64, and macOS x86_64 with correct Rust targets.
- [ ] Linux-only package installation cannot execute on other runners.
- [ ] Signing/notarization variables reach the release action without being logged.
- [ ] Dependency automation groups related GitHub Actions, npm, and Cargo families.
- [ ] Releases remain drafts and matrix failures do not cancel other platform bundles.

## Verification commands

```powershell
pnpm install --frozen-lockfile
pnpm exec tsc --noEmit
pnpm build
cargo check --manifest-path src-tauri/Cargo.toml --all-targets --locked
cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets --locked -- -D warnings
$ci = Get-Content .github/workflows/ci.yml -Raw
$release = Get-Content .github/workflows/release.yml -Raw
$dependabot = Get-Content .github/dependabot.yml -Raw
if ($ci -notmatch '(?ms)pull_request:.*?branches:\s*\[main\]' -or $ci -notmatch '(?ms)push:.*?branches:\s*\[main\]' -or $ci -notmatch '(?ms)^concurrency:.*?cancel-in-progress:\s*true') { throw 'main-branch triggers or cancellation missing' }
foreach ($required in @('pnpm install --frozen-lockfile', 'pnpm exec tsc --noEmit', 'pnpm build', 'cargo check --all-targets --locked', 'cargo clippy --all-targets --locked -- -D warnings', 'libwebkit2gtk-4.1-dev')) { if ($ci -notmatch [regex]::Escape($required)) { throw "CI gate missing: $required" } }
foreach ($required in @('ubuntu-22.04', 'windows-latest', 'aarch64-apple-darwin', 'x86_64-apple-darwin', 'fail-fast: false', "if: matrix.platform == 'ubuntu-22.04'", 'TAURI_SIGNING_PRIVATE_KEY', 'APPLE_API_KEY_PATH', 'releaseDraft: true')) { if ($release -notmatch [regex]::Escape($required)) { throw "release contract missing: $required" } }
foreach ($ecosystem in @('github-actions', 'npm', 'cargo')) { if ($dependabot -notmatch "package-ecosystem:\s*$ecosystem") { throw "Dependabot missing $ecosystem" } }
foreach ($group in @('ai-sdk:', 'codemirror:', 'tauri:', 'xterm:', 'radix:')) { if ($dependabot -notmatch [regex]::Escape($group)) { throw "Dependabot group missing: $group" } }
if (-not (Test-Path .github/CODEOWNERS)) { throw 'CODEOWNERS missing' }
$bundle = Get-Content src-tauri/tauri.conf.json -Raw | ConvertFrom-Json
if ($bundle.bundle.windows.webviewInstallMode.type -ne 'downloadBootstrapper' -or $bundle.bundle.windows.nsis.displayLanguageSelector -ne $false) { throw 'Windows bootstrapper packaging adjustment missing' }
```

## Scoring: pass / partial / fail notes

- **pass** - PR and release workflows are valid, complete, correctly scoped, and reproducible.
- **partial** - core matrix/gates exist but one platform, lock, signing, or grouping requirement is wrong.
- **fail** - workflow is invalid, secrets leak, required checks are absent, or platform setup is unguarded.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet a9bf5700564ee412ab21b16b504d3eaba6199b41 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference adds CODEOWNERS, grouped Dependabot configuration, a two-job PR workflow, four-entry release matrix, platform guards, signing inputs, and a small Windows bootstrapper packaging adjustment. Inspect with `git -C "C:\terax-ai" show 4dc87cf9f16e57d35452aa857973bb68d49fb810`.
