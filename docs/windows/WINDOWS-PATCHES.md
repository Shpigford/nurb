# Windows-specific patch register

This file records intentional downstream changes found in the current working tree.

## Runtime and platform

- `src/nurb/platform/**`: central Windows paths, executable naming, and subprocess helpers.
- `src/nurb/checks.py`: global config now uses the platform path surface.
- `src/nurb/server.py`: latest-version cache uses the platform cache directory.
- `src/nurb/cli.py`: Windows launcher, socket probing, and path-aware messages.
- `src/nurb/slicing.py`: Windows slicer discovery and user-profile locations.

## Desktop process model

- `desktop/src-tauri/src/process.rs`: central child-process ownership and tree termination.
- `acp.rs`, `agents.rs`, `provision.rs`, and `supervisor.rs`: use the centralized process layer.
- `acp/sandbox.rs`: Seatbelt remains on macOS; Windows currently runs without an equivalent sandbox boundary and this limitation is explicit.

## Runtime layout

- `env.rs`: Windows `Scripts/`, `node.exe`, npm layout, adapter JS entry resolution, and native Codex path resolution.
- The inherited Windows `PATH` is split into individual entries before being rebuilt; this was corrected during the audit.
- `provision.rs`: Windows Node archive selection, checksum validation, extraction, OS identification, and process cleanup.
- `desktop/scripts/stage.py`: cross-platform staging and verified uv acquisition.

## Desktop identity and UX

- `pyproject.toml` `[project.urls]` names the fork (`Alot1z/nurb-windows`) as Repository/Issues and keeps upstream as a separate `Upstream` link, so packaging metadata and bug reports land on the fork. Merge strategy: take the fork side on `pyproject.toml` conflicts; it does not affect the uv lock.
- Windows removes macOS overlay-titlebar behavior and DMG packaging.
- Project-name validation rejects `\\` on Windows.
- About/help links point at `Alot1z/nurb-windows`.
- Windows wording uses Explorer, Recycle Bin, PowerShell, and PC where appropriate.

## Release/update security

The inherited upstream updater was removed and replaced with a fork-owned channel: the plugin now points only at `Alot1z/nurb-windows` releases (`latest.json` on the fork's releases), signed by a fork keypair whose public key is committed (`desktop/signing/tauri-updater.key.pub` -> `tauri.conf.json` `plugins.updater.pubkey`) and whose private key exists only as a CI secret plus a gitignored local copy. The Windows surface is the rail's "check for updates" button; the macOS "Check for Updates…" menu item forwards to the same flow. `.github/workflows/windows-release.yml` builds the signed installer on the `v*` tag and publishes the installer, `.sig`, and `latest.json` to the fork's release. Builds fail loudly when the signing key is absent, so an unsigned update channel cannot ship. See `docs/windows/RELEASE.md` for the secret setup.

## Extension system (developer-only)

New fork-owned capability, additive to the desktop and Python layers; upstream `src/nurb` behavior is unchanged except one new subcommand.

- `desktop/src-tauri/src/extensions.rs`: generic extension registry (manifests, declarative lookups, enable/disable state, version gate). Extensions are developer-only and disabled by default.
- `desktop/src-tauri/src/terminal.rs`: ConPTY/pty terminal host via `portable-pty` (new dependency, added to `Cargo.toml`). Byte-only transport: user keystrokes in, child output out, no parsing, no injection. Spawns only registered extension manifests with `--cwd <project>` as the single substitution.
- `desktop/src-tauri/src/lib.rs`: new commands (`extension_statuses`, `set_extension_enabled`, `open_terminal_extension`, `launch_external_extension`, `terminal_input`, `terminal_resize`, `terminal_close`) and shutdown cleanup.
- `desktop/src/TerminalPanel.tsx` (xterm.js, `xterm` + `@xterm/addon-fit` added to `desktop/package.json`), `desktop/src/ExtensionsModal.tsx`, rail entry in `App.tsx`, styles in `App.css`.
- `src/nurb/mcp.py` + `nurb mcp` subcommand in `src/nurb/cli.py`: a stdio MCP server whose tools are the CLI commands themselves (same argparse Namespace, same `cmd_*` functions, output captured). `tests/test_mcp.py` drives it as a real subprocess. Merge strategy for `cli.py`: additive subparser only, no changes to existing commands.
- Extensions are developer-only and off by default; nothing in the extension system itself depends on external permissions.

## Upstream publish workflow removed from the fork

`.github/workflows/publish.yml` (inherited from upstream) was deleted. It is upstream's release ceremony: on a version bump it publishes the `nurb` wheel to PyPI over trusted publishing and creates the GitHub release. On the fork it cannot work and does harm: the fork's `pypi` environment is not a PyPI publisher for Shpigford's project, so a version bump makes a red run; and the "already on PyPI, tagging only" path created source-only releases with no assets and no notes, which is exactly the misleading `v0.20.0` release on the fork. The fork's release flow is one workflow: push the `vX.Y.Z` tag, and `.github/workflows/windows-release.yml` builds the signed installer and updater artifacts and creates the release with real assets. If the fork ever needs its own PyPI publishing, that belongs in a new fork-owned workflow, not a revived copy of upstream's.

## Chat runtime health check (Windows hardening)

`provision.rs` health probes now retry once after a short pause: a freshly
extracted binary can fail its very first spawn on Windows while the real-time
scanner holds the image, and one retry turns that transient into a successful
provision instead of the old "the agent install is missing a platform-native
CLI" error and a full re-download. The probe output file is overwritten rather
than created exclusively, because Windows recycles PIDs fast enough that a
stale `.health-*` file left by a killed provisioning could collide and fail
every probe with no explanation. The error message now says what to do (retry
or relaunch) instead of misreporting a missing CLI when any of the five probes
(node, both adapters, both native CLIs) was the actual failure.

## Shipped agent docs name both platforms

`src/nurb/doctrine.md`, `src/nurb/agents.md`, `src/nurb/skill.md`, and
`skills/nurb/SKILL.md` now name the per-user config file as
`%APPDATA%\nurb\config.toml` on Windows (with `~/.config/nurb/config.toml`
elsewhere) and the launcher as `viewer.cmd` on Windows, instead of Unix-only
paths. Without this, a Windows agent followed the skill and wrote its standing
answers to a directory nurb never reads. The wording is platform-neutral so it
is an upstream-compatible change, but it does touch the four SAFE-category
files; the one-body test (`test_the_skill_is_the_shim_with_a_trigger_on_top`)
keeps skill.md, SKILL.md, and the agents.md body from drifting.

## Windows-only Python fixes worth remembering

- `src/nurb/platform/paths.py` `home_dir()` honors `HOME` even on Windows, where `pathlib.Path.home()` only reads `USERPROFILE`. This is what makes the skill-install tests (which monkeypatch `HOME`) pass, and it is the right semantic for agents that set `HOME` to stage a skill.
- `src/nurb/cli.py` writes `viewer.cmd` with `newline=""` and `open(..., "w", newline="")` so the launcher stays exactly CRLF instead of becoming CRCRLF on Windows text-mode writes; `nurb launcher` prints the Explorer double-click path.
- The dev-server port probe uses `SO_EXCLUSIVEADDRUSE` on Windows (upstream's `SO_REUSEADDR` permits binding over a live listener there, so the "already serving" guard never fired).

## Release-gate script

`tools/release_gate.py` runs the post-PR release-readiness checks the
maintainer was doing by hand in one invocation. It does not run pytest
on purpose (the suite is ~8 minutes and lives in CI); it covers the cheap
invariants instead: tracking hygiene (no private keys, no leaked
private dev space), updater pin (no Shpigford endpoint, embedded pubkey
matches committed key), the staging script parses, the build
toolchain is reachable. Exit code is the count of failed checks; zero
means the fork is ready for a release-gate PR.

## Authenticode signing pipelined, certificate EXTERNAL

`desktop/scripts/stage.py` now exposes `check_authenticode_signing()`,
called from `__main__` after `main()` succeeds. Behavior is fully
env-gated: when `NURB_WINDOWS_AUTHENTICODE_REQUIRED` is unset,
authentiocde is a no-op (local dev builds do not sign); when set to
`1`, signing must succeed. The pipeline reads the cert path from
`NURB_WINDOWS_AUTHENTICODE_PFX`, an optional password from
`NURB_WINDOWS_AUTHENTICODE_PFX_PASSWORD`, and the timestamp authority
from `NURB_WINDOWS_AUTHENTICODE_TIMESTAMP_URL` (default DigiCert), and
invokes `signtool sign /fd sha256 /td sha256` from the Windows SDK. A
missing cert or missing `signtool.exe` fails loudly so the release
pipeline never silently ships an unsigned executable when it asked for
a signed one. The certificate itself is EXTERNAL: this repo never
stores it, only references the path the CI environment passes in.

## Maintenance policy

Prefer adding future Windows behavior behind platform boundaries instead of modifying upstream-core logic. Every new Windows-only deviation should be added here with a reason and merge strategy.
