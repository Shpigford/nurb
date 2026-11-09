# nurb desktop

A Tauri shell around nurb: project rail, agent chat column, and the live viewer in one window.

## Dev setup

Rust toolchain, Node 22+, uv, and Xcode command line tools. Then:

```
npm install            # at the repo root: it is an npm workspace, and the lockfile lives there
npm run tauri dev      # from this directory
```

Debug builds run nurb out of this checkout (`uv run --project <repo> nurb dev`) and the ACP adapters through PATH `npx`, so nothing needs provisioning. `cargo test` inside `src-tauri/` needs `scripts/stage.sh` to have run once (the build script wants the uv sidecar); any `tauri dev` or `tauri build` runs it for you.

## Provisioning model

Release builds never touch the dev environment. On first launch the app provisions everything into its app data directory (`~/Library/Application Support/dev.nurb.desktop`):

- `python/`, `env/`: a managed CPython and a venv holding the bundled nurb wheel plus its hash-pinned lock, installed by the bundled uv sidecar.
- `node/`, `adapters/`: the pinned Node LTS (downloaded from nodejs.org, checksum-verified), the Claude and Codex ACP adapters, and the official Gemini CLI, installed on the user's machine with `npm ci` from a committed integrity lock. Gemini speaks ACP natively through `--acp`; the app validates its Google AI Studio API key through ACP and stores the key in macOS Keychain, never app preferences. These packages are deliberately not bundled: the Claude Code binary inside `@anthropic-ai/claude-agent-sdk` is all-rights-reserved and must not be redistributed. Cursor and Grok speak ACP natively and are never provisioned at all: the app finds the CLI the vendor's own installer put on the machine (`~/.local/bin/cursor-agent`, `~/.grok/bin/grok`, then the PATH of the user's login shell, so Homebrew and npm installs count too; never the bare `agent`, which Grok's installer also claims). An app opened from Finder only gets launchd's bare PATH, so the app asks the login shell once at launch and hands that PATH to every agent it spawns. Until it exists the agent stays out of the rail; the rail's "need another agent?" help lists the missing ones with their installers.
- `provisioned.json`: what was installed, compared per component on every launch. A changed Python lock rebuilds the venv, a changed wheel on the same lock replaces only nurb inside it (no network needed, so an update works offline), and a changed Node version or adapter lock redoes only its own component; a broken venv is deleted and rebuilt.

A serve already answering for the home is adopted, except one left by a crashed app (its parent is launchd) on another version, which is stopped and replaced so an update never keeps talking to an old engine.

`scripts/stage.sh` stages the bundle inputs before every build: the nurb wheel from this checkout, the dependencies as pinned by `engine/uv.lock` (`uv export`), the committed adapter manifest and lock, and the uv binaries for both darwin targets (skipped once downloaded).

Debug-build test overrides, never compiled into release: `NURB_DESKTOP_PROVISIONED=1` makes a debug build use the provisioned environment, and `NURB_DESKTOP_DATA=<dir>` points the whole app (registry, sessions, provisioned env) at a scratch directory.

## Release

The engine and the app share one version and one release: `uv version X.Y.Z` in `engine/`, the matching SemVer in `src-tauri/tauri.conf.json`, `packages/ui/package.json`, and both exact `@nurb/ui` workspace pins (tests enforce the set), merge, then run `scripts/release.sh`. The script builds the desktop half for Apple silicon and Intel, signed and notarized (credentials from `desktop/.env`, see `.env.example`), verifies each chain (`codesign --verify --deep --strict`, `spctl --assess`, `stapler validate`), then uploads `nurb.dmg` for Apple silicon and `nurb-intel.dmg` for Intel Macs plus target-specific updater archives to the `vX.Y.Z` GitHub release, which it tags and creates as a draft and publishes once every file is up, then refreshes `latest.json` on the rolling `desktop-latest` prerelease, the feed installed apps poll. It runs one release at a time, fails closed when the current feed cannot be read, resumes a draft a failed run left behind, and never replaces artifacts for a version already published.

Updates are signed with the key from `tauri signer generate` (path in `.env`; the public key lives in `tauri.conf.json`). Losing that private key means shipped apps can never update again.

Releases run from a Mac with the Developer ID certificate in the keychain, the same way the other Sabotage Media apps ship; there is no CI signing. The script builds `aarch64-apple-darwin` and `x86_64-apple-darwin`. `latest.json` carries both updater entries, so installed apps receive the archive for their architecture.
