# Task 15 - Defend AI proxy from SSRF

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `06d0a8b8e47b209d9a8426b6bad9393b1fa25825`
Start commit: `2bfffae734b672ffefffe1edc040a87ce8568191`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

The renderer's AI HTTP proxy accepts provider URLs and headers, allowing requests toward metadata services, loopback or private networks, unsafe URL forms, and hop-by-hop or authority-changing headers. Enforce the policy in the native request layer, including DNS results and connection resolution. Keep local model providers usable only through an explicit private-network opt-in, and pass that intent through the TypeScript wrapper without making arbitrary calls permissive.

## Success criteria (checkable)

- [ ] Only HTTP(S) URLs without userinfo are accepted; metadata and non-routable destinations are always denied
- [ ] Loopback/private addresses require explicit opt-in, including literal IPs and resolved hostnames
- [ ] Redirects or DNS changes cannot bypass the address policy, and unsafe request headers are rejected
- [ ] Local model callers opt in narrowly while the default proxy remains public-network only
- [ ] Rust network checks and frontend tests/typecheck pass

## Verification commands

`cargo test --manifest-path src-tauri/Cargo.toml modules::net && pnpm test && pnpm exec tsc --noEmit`

## Scoring: pass / partial / fail notes

- **pass** - URL, DNS, redirect, connection, header, and explicit-local-provider boundaries are all enforced.
- **partial** - obvious metadata/private targets are blocked but rebinding, redirects, headers, or opt-in scope remain weak.
- **fail** - attacker-controlled requests can reach protected networks, local providers break globally, or checks fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\terax-ai" show 06d0a8b8e47b209d9a8426b6bad9393b1fa25825` (graders only - never shown to a model).

The reference centralizes URL/host/IP/header checks in `src-tauri/src/modules/net.rs`, disables unsafe resolution paths, carries `allowPrivateNetwork` through proxy IPC, and opts in only local provider clients.
