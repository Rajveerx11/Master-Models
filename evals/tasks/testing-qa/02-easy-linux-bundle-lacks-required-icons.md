# Task 02 - Linux bundle lacks required icons

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `cdad1a3ecb7cdfb6a278c7ae38b67d9e132d50bb`
Start commit: `779688efc641cdd930a7c965920996a7effc6d0d`
Difficulty: **easy**
Category: release packaging

## Prompt (given to the agent verbatim)

The desktop release configuration names only a Windows icon, causing Linux AppImage packaging to miss required square PNG assets. Configure the existing cross-platform icon set and make the generated release title use the product name shown to users. Keep bundle targets and release publication behavior unchanged.

## Success criteria (checkable)

- [ ] Bundle configuration includes the existing 32px, 128px, high-density 128px, macOS, and Windows icon assets.
- [ ] Linux packaging can select square PNG icons instead of relying on an ICO file.
- [ ] Release drafts use the product-facing Tessera name.
- [ ] Existing bundle targets, tag handling, draft status, and prerelease status remain unchanged.
- [ ] Tauri configuration remains valid JSON and the renderer still builds.

## Verification commands

```powershell
$config = Get-Content apps/desktop/src-tauri/tauri.conf.json -Raw | ConvertFrom-Json
$expected = @('icons/32x32.png', 'icons/128x128.png', 'icons/128x128@2x.png', 'icons/icon.icns', 'icons/icon.ico')
$actual = @($config.bundle.icon)
if ($actual.Count -ne $expected.Count -or (Compare-Object $expected $actual)) { throw 'bundle.icon does not contain the exact cross-platform icon set' }
foreach ($icon in $expected) { if (-not (Test-Path (Join-Path apps/desktop/src-tauri $icon))) { throw "missing icon: $icon" } }
$release = Get-Content .github/workflows/release.yml -Raw
if ($release -notmatch "releaseName:\s*'Tessera \$\{\{ github\.ref_name \}\}'" -or $release -match "releaseName:\s*'Testing IDE") { throw 'release display name is not Tessera' }
if ($release -notmatch 'releaseDraft:\s*true' -or $release -notmatch 'prerelease:\s*false' -or $release -notmatch 'tagName:\s*\$\{\{ github\.ref_name \}\}') { throw 'release publication semantics changed' }
pnpm --filter @testing-ide/desktop run vite:build
```

## Scoring: pass / partial / fail notes

- **pass** - complete existing icon set is configured, release naming is correct, and packaging settings remain intact.
- **partial** - Linux receives a usable PNG but cross-platform icons, naming, or validation is incomplete.
- **fail** - AppImage still depends only on ICO, paths do not exist, JSON/workflow is invalid, or release behavior changes.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 779688efc641cdd930a7c965920996a7effc6d0d -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference expands `bundle.icon` in `apps/desktop/src-tauri/tauri.conf.json` to the existing PNG, ICNS, and ICO assets and changes only the release display name in `.github/workflows/release.yml`. Inspect with `git -C "C:\Testing IDE" show cdad1a3ecb7cdfb6a278c7ae38b67d9e132d50bb`.
