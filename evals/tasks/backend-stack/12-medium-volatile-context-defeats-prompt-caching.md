# Task 12 - Volatile context defeats prompt caching

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `3e4b7d25fbb3f08d92a8c32123b534b84d6d7f63`
Start commit: `4d3df392a809f99df03634c1df0f2da6fef57687`
Difficulty: **medium**

## Prompt (given to the agent verbatim)

The agent rebuilds a wrapper on every send and injects changing terminal state into the user message, preventing useful provider prompt caching. Move to a direct streaming pipeline with a stable system prefix, a separate volatile environment block, provider-aware cache markers, abort propagation, usage reporting, and the same tools, plan-mode behavior, step labels, and UI message stream contract.

## Success criteria (checkable)

- [ ] Sending uses a direct streaming call and converts UI history to model messages
- [ ] Stable persona, custom instructions, and project memory remain in a stable system prefix
- [ ] Terminal/workspace context is a separate bounded environment system block
- [ ] Explicit cache breakpoints apply only where the provider requires them
- [ ] Abort signals, step callbacks, tool wiring, plan mode, and UI stream conversion still work
- [ ] Usage deltas include input, output, and cache-read tokens
- [ ] `pnpm exec tsc --noEmit` passes

## Verification commands

```powershell
pnpm exec tsc --noEmit
```

## Scoring: pass / partial / fail notes

- **pass** - caching boundaries improve while all streaming and agent contracts remain intact.
- **partial** - direct streaming works but cache placement, volatile context, aborts, usage, or callbacks regress.
- **fail** - transport breaks, provider behavior leaks across providers, or type checking fails.

## Graders-only reference evidence

Run this pipeline discriminator:

```powershell
$agent = Get-Content src/modules/ai/lib/agent.ts -Raw
$transport = Get-Content src/modules/ai/lib/transport.ts -Raw
foreach ($marker in @('export async function runAgentStream', 'convertToModelMessages', 'buildStableSystem', 'applyCacheBreakpoints', 'cacheControl', 'step.usage')) { if (-not $agent.Contains($marker)) { exit 1 } }
if (-not $transport.Contains('MAX_TERMINAL_CHARS = 4_000') -or -not $transport.Contains('formatEnvBlock') -or -not $transport.Contains('runAgentStream')) { exit 1 }
```

The direct-streaming and cache-boundary markers are absent at `4d3df392a809f99df03634c1df0f2da6fef57687`; all pass at `3e4b7d25fbb3f08d92a8c32123b534b84d6d7f63`.

The reference replaces the experimental agent/transport wrapper with `streamText`, constructs stable and volatile system messages separately, adds Anthropic-only cache markers, reports usage, and reduces the terminal snapshot cap. Inspect with `git diff 4d3df392a809f99df03634c1df0f2da6fef57687 3e4b7d25fbb3f08d92a8c32123b534b84d6d7f63 -- src/modules/ai/lib/agent.ts src/modules/ai/lib/transport.ts`.
