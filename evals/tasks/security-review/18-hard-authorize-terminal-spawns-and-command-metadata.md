# Task 18 - Authorize terminal spawns and command metadata

Source repository: `terax-ai`
Source checkout: `C:\terax-ai`
Reference commit: `b5f65346882cd5527e79bf0d18b242d17cfc236d`
Start commit: `dd92eff7f95cb36c6f3fb3d3d25b7d705d2bf812`
Difficulty: **hard**

## Prompt (given to the agent verbatim)

Terminal and background-shell creation accepts working directories without proving they belong to an authorized workspace. Command completion also trusts a fixed output marker, and Git file operations accept pathspec syntax that can reinterpret user paths. Apply the same canonical workspace authorization to every spawn route, make completion markers unpredictable per session, and reject path values that Git can parse as magic or controls.

## Success criteria (checkable)

- [ ] PTY, one-shot, persistent, and background shell routes authorize canonical working directories against registered workspaces
- [ ] Missing paths and symlink escapes are rejected while authorized roots and descendants remain valid
- [ ] Each shell session uses an unpredictable marker and only its own marker can update captured working directory metadata
- [ ] Empty, colon-bearing, NUL, newline, carriage-return, and tab Git pathspecs are rejected before Git invocation
- [ ] Focused Rust tests cover all three boundaries and the crate test suite passes

## Verification commands

`cargo test --manifest-path src-tauri/Cargo.toml`

## Scoring: pass / partial / fail notes

- **pass** - every spawn, metadata, and Git path boundary closes consistently with regression tests.
- **partial** - two boundaries close but one route, link case, marker case, or pathspec case remains.
- **fail** - unauthorized execution or metadata spoofing remains possible, Git magic is accepted, or tests fail.

## Graders-only reference evidence

Reference solution: `git -C "C:\terax-ai" show b5f65346882cd5527e79bf0d18b242d17cfc236d` (graders only - never shown to a model).

The reference adds central spawn authorization, wires it through all shell entry points, stores a generated session marker, and validates Git pathspecs before repository resolution.
