# Task 05 - Build tools are classified as runtime dependencies

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `567b022685ce652a95458633049243004d19a8af`
Start commit: `d4abe401d30291d5800a26b039f4e1a174782853`
Difficulty: **easy**
Category: dependency/build verification

## Prompt (given to the agent verbatim)

The package manifest classifies several styling and scaffolding tools as production dependencies even though they are needed only while developing or building the app. Move only build-time packages to the correct dependency section, preserve every version and resolved package, and keep frozen installation plus the production build green.

## Success criteria (checkable)

- [ ] Tailwind Vite integration, Tailwind CSS, animation CSS tooling, and the UI scaffolding CLI are development dependencies.
- [ ] Runtime imports remain in production dependencies.
- [ ] No package version or resolved lockfile version changes.
- [ ] Frozen lockfile installation succeeds without drift.
- [ ] Type checking, tests, and production build still pass.

## Verification commands

```powershell
pnpm install --frozen-lockfile
pnpm exec tsc --noEmit
pnpm test
pnpm build
```

## Scoring: pass / partial / fail notes

- **pass** - only build-time packages move sections, lockfile importer matches, and all checks pass.
- **partial** - classification improves but one tool, lock entry, or verification requirement is missed.
- **fail** - runtime packages move incorrectly, versions change, frozen install fails, or build/test behavior regresses.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet d4abe401d30291d5800a26b039f4e1a174782853 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference moves `@tailwindcss/vite`, `shadcn`, `tailwindcss`, and `tw-animate-css` from dependencies to devDependencies in `package.json` and mirrors only that classification in `pnpm-lock.yaml`. Inspect with `git -C "C:\terax-ai" show 567b022685ce652a95458633049243004d19a8af`.
