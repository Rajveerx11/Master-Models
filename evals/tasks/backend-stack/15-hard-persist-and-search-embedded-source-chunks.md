# Task 15 - Persist and search embedded source chunks

Source repository: `testing-ide`
Source checkout: `C:\Testing IDE`
Reference commit: `e92c34c57d947a9537536fce2b3f73666911682c`
Start commit: `16dd9dd2509764c097d3ec96d9ae425a5dfb36f5`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Add the repository layer that atomically persists semantic source chunks with their embeddings and retrieves project-scoped nearest matches. Store vectors as portable binary data, preserve chunk metadata, reject inconsistent dimensions, enforce a per-project/provider/dimension capacity, and cap result counts. Similarity search must isolate providers and dimensions, handle zero or malformed vectors safely, order strongest matches first, and expose enough metadata for later reranking.

## Success criteria (checkable)

- [ ] Batch inserts are atomic and return generated identifiers in input order
- [ ] Vector encoding round-trips finite `f32` values in a stable byte order
- [ ] Insert and query dimensions are validated before comparison
- [ ] Search is scoped by project, embedding provider, and dimension
- [ ] Zero-norm and malformed stored vectors are skipped without panics or NaN results
- [ ] Results are similarity-sorted and bounded by a server-side top-K cap
- [ ] Per-tuple counts and capacity limits are enforced
- [ ] Focused repository tests and strict Clippy pass

## Verification commands

```powershell
$output = cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib chunk_repo 2>&1; $code = $LASTEXITCODE; $output | Write-Output; if ($code -ne 0 -or $output -notmatch '11 passed') { exit 1 }
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets -- -D warnings
```

## Scoring: pass / partial / fail notes

- **pass** - atomic persistence and robust, isolated cosine retrieval satisfy all limits and edge cases.
- **partial** - common insert/search works but one isolation, validation, atomicity, or bound is missing.
- **fail** - vectors cross scopes/dimensions, partial batches persist, malformed data panics, or checks fail.

## Graders-only reference evidence

The reference adds one repository module plus registration with eleven focused tests for binary round trips, atomic inserts, tuple isolation, ordering, bounds, invalid dimensions, malformed vectors, and zero norms. Inspect with `git diff 16dd9dd2509764c097d3ec96d9ae425a5dfb36f5 e92c34c57d947a9537536fce2b3f73666911682c -- apps/desktop/src-tauri/src/repositories/chunk_repo.rs apps/desktop/src-tauri/src/repositories/mod.rs`.
