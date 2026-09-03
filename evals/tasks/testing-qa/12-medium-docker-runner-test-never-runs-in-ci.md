# Task 12 - Docker runner test never runs in CI

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `de4564870f88d4a9805cbfafd692a5fd346aeac7`
Start commit: `73b62f7c67871183b93fee60533d48ed506d2f28`
Difficulty: **medium**
Category: deterministic integration gate

## Prompt (given to the agent verbatim)

The real Docker sandbox test is ignored by the normal unit suite and its runner image is never built in CI, so image/runtime regressions can ship unnoticed. Add a blocking deterministic gate that builds or restores the exact runner image, executes the ignored test, and remains resilient to Docker Hub rate limits.

## Success criteria (checkable)

- [ ] CI has a dedicated blocking sandbox-runner job with a bounded timeout.
- [ ] The runner image is built from the repository Dockerfile before the ignored integration test runs.
- [ ] A cache keyed by Dockerfile content avoids routine registry pulls.
- [ ] Optional registry credentials are used only when available and only on cache miss.
- [ ] Transient build failures receive finite backoff retries.
- [ ] The existing ignored Docker test is explicitly executed and no LLM/external service is required.

## Verification commands

```powershell
docker build -t tessera-runner-js -f apps/desktop/src-tauri/docker/Dockerfile.runner-js apps/desktop/src-tauri/docker
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --lib -- --ignored docker_runner_executes
```

## Scoring: pass / partial / fail notes

- **pass** - real sandbox execution becomes a bounded, blocking, cache-aware gate.
- **partial** - test runs but registry resilience, blocking semantics, or reproducibility is weak.
- **fail** - only unit tests run, ignored test stays unreachable, or gate silently tolerates failure.

## Graders-only reference evidence

Hidden start-state guard: from the source checkout, run `git diff --quiet 73b62f7c67871183b93fee60533d48ed506d2f28 -- .; if ($LASTEXITCODE -eq 0) { exit 1 }`. This must fail on the untouched start state and pass on the reference change.

Reference adds `sandbox-runner-test` to `.github/workflows/ci.yml` with image cache/load, optional login, three build attempts, and explicit ignored-test execution. Inspect with `git -C "C:\Testing IDE" show de4564870f88d4a9805cbfafd692a5fd346aeac7`.
