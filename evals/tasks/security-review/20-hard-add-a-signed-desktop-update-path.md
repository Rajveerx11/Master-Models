# Task 20 - Add a signed desktop update path

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `a5599e04ab6e609ad51833c9dbcf81d55ea4ba3c`
Start commit: `b942e82e25ce1ef6849160a784d6f3428bad2fa6`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Add in-app desktop updates without creating an unsigned remote-code path. Configure release artifacts and a fixed HTTPS metadata endpoint with signature verification, grant only updater capability, and expose a user-facing check/download/install/relaunch flow. Automatic checks should be rate-limited, manual checks should bypass that throttle, progress and errors should be explicit, and mobile builds must remain unaffected.

## Success criteria (checkable)

- [ ] Desktop builds produce updater artifacts and verify metadata/packages against a configured public signing key
- [ ] Update metadata comes from one fixed HTTPS release endpoint and only required desktop capabilities/plugins are enabled
- [ ] Startup checks are throttled, manual checks remain available, and state covers checking, current, available, downloading, ready, and error cases
- [ ] Installation reports byte progress, relaunches only after successful install, and does not initialize desktop-only plugins on mobile
- [ ] Version/config/dependencies stay consistent and Rust/frontend checks pass

## Verification commands

`pnpm exec tsc --noEmit && cargo check --manifest-path src-tauri/Cargo.toml`

## Scoring: pass / partial / fail notes

- **pass** - update chain is signed, narrowly permissioned, fixed-endpoint, platform-safe, and complete in UI lifecycle.
- **partial** - update flow works but signing, capability scope, throttling, progress, or platform gating is incomplete.
- **fail** - unsigned/untrusted updates can install, permissions are broad, versions diverge, or checks fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\terax-ai" show a5599e04ab6e609ad51833c9dbcf81d55ea4ba3c` (graders only - never shown to a model).

The reference enables Tauri updater artifacts, a minisign public key and fixed GitHub endpoint, desktop-only updater/process plugins, a throttled update hook, and an install-progress dialog.
