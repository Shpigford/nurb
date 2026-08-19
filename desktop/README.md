# nurb desktop

A Tauri shell around nurb: project rail, agent chat column, and the live viewer in one window.

## Dev setup

Rust toolchain, Node 22+, uv, and Xcode command line tools. Then:

```
npm install
npm run tauri dev
```

Debug builds run nurb out of this checkout (`uv run --project <repo> nurb dev`) and the ACP adapters through PATH `npx`, so nothing needs provisioning. `cargo test` inside `src-tauri/` needs `scripts/stage.sh` to have run once (the build script wants the uv sidecar); any `tauri dev` or `tauri build` runs it for you.

## Provisioning model

Release builds never touch the dev environment. On first launch the app provisions everything into its app data directory (`~/Library/Application Support/dev.nurb.desktop`):

- `python/`, `env/`: a managed CPython and a venv holding the bundled nurb wheel plus its hash-pinned lock, installed by the bundled uv sidecar.
- `node/`, `adapters/`: the pinned Node LTS (downloaded from nodejs.org, checksum-verified), the Claude and Codex ACP adapters, and the official Gemini CLI, installed on the user's machine with `npm ci` from a committed integrity lock. Gemini speaks ACP natively through `--acp`; the app validates its Google AI Studio API key through ACP and stores the key in macOS Keychain, never app preferences. These packages are deliberately not bundled: the Claude Code binary inside `@anthropic-ai/claude-agent-sdk` is all-rights-reserved and must not be redistributed. Cursor and Grok speak ACP natively and are never provisioned at all: the app finds the CLI the vendor's own installer put on the machine (`~/.local/bin/agent`, `~/.grok/bin/grok`, then PATH). Until it exists the agent stays out of the rail; the rail's "need another agent?" help lists the missing ones with their installers.
- `provisioned.json`: what was installed, compared per component on every launch. A changed wheel payload, Python lock, Node version, or adapter lock redoes only its own component; a broken venv is deleted and rebuilt.

`scripts/stage.sh` stages the bundle inputs before every build: the nurb wheel from this checkout, a `uv pip compile --universal --generate-hashes` lock, the committed adapter manifest and lock, and the uv binaries for both darwin targets (skipped once downloaded).

Debug-build test overrides, never compiled into release: `NURB_DESKTOP_PROVISIONED=1` makes a debug build use the provisioned environment, and `NURB_DESKTOP_DATA=<dir>` points the whole app (registry, sessions, provisioned env) at a scratch directory.

## Release

The engine and the app share one version and one release: `uv version X.Y.Z` at the repo root, the matching `version` in `src-tauri/tauri.conf.json` (a test enforces they agree, alongside the skill files), merge, then run `scripts/release.sh`. publish.yml handles PyPI and creates the `vX.Y.Z` release on merge; the script builds the desktop half for Apple silicon and Intel, signed and notarized (credentials from `desktop/.env`, see `.env.example`), verifies each chain (`codesign --verify --deep --strict`, `spctl --assess`, `stapler validate`), uploads `nurb.dmg` for Apple silicon and `nurb-intel.dmg` for Intel Macs plus target-specific updater archives, and refreshes `latest.json` on the rolling `desktop-latest` prerelease that installed apps poll. It refuses to upload twice for one version.

Updates are signed with the key from `tauri signer generate` (path in `.env`; the public key lives in `tauri.conf.json`). Losing that private key means shipped apps can never update again.

Releases run from a Mac with the Developer ID certificate in the keychain, the same way the other Sabotage Media apps ship; there is no CI signing. The script builds `aarch64-apple-darwin` and `x86_64-apple-darwin`. `latest.json` carries both updater entries, so installed apps receive the archive for their architecture.
