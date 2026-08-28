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

`scripts/stage.sh` stages the bundle inputs before every build: the nurb wheel from this checkout, a `uv pip compile --universal --generate-hashes` lock, the committed adapter manifest and lock, and the uv binaries for the targets this host builds, both darwin triples on a Mac and the host triple on Linux (skipped once downloaded).

Debug-build test overrides, never compiled into release: `NURB_DESKTOP_PROVISIONED=1` makes a debug build use the provisioned environment, and `NURB_DESKTOP_DATA=<dir>` points the whole app (registry, sessions, provisioned env) at a scratch directory.

## Release

The engine and the app share one version and one release: `uv version X.Y.Z` at the repo root, the matching `version` in `src-tauri/tauri.conf.json` (a test enforces they agree, alongside the skill files), merge, then run `scripts/release.sh`. publish.yml handles PyPI and creates the `vX.Y.Z` release on merge; the script builds the desktop half for Apple silicon and Intel, signed and notarized (credentials from `desktop/.env`, see `.env.example`), verifies each chain (`codesign --verify --deep --strict`, `spctl --assess`, `stapler validate`), uploads `nurb.dmg` for Apple silicon and `nurb-intel.dmg` for Intel Macs plus target-specific updater archives, and refreshes `latest.json` on the rolling `desktop-latest` prerelease that installed apps poll. It refuses to upload twice for one version.

Updates are signed with the key from `tauri signer generate` (path in `.env`; the public key lives in `tauri.conf.json`). Losing that private key means shipped apps can never update again.

Releases run from a Mac with the Developer ID certificate in the keychain, the same way the other Sabotage Media apps ship; there is no CI signing. The script builds `aarch64-apple-darwin` and `x86_64-apple-darwin`.

Linux is the same release from a second machine: `scripts/release-linux.sh` builds the `.deb` and the AppImage for the host architecture and uploads them into that same `vX.Y.Z` release. Tauri links against the host's system webview, which is why it cannot come off the Mac. It needs the updater key and nothing else, since there is no notarization step.

Linux has no updater tarball: both packages are self-contained updater artifacts that the bundler signs where they sit. The feed carries two entries per architecture, `linux-<arch>` for the AppImage and `linux-<arch>-deb` for the `.deb`, because the updater asks for its own package format first and a copy installed from the `.deb` cannot install an AppImage.

`scripts/common.sh` holds what both release scripts do the same way: the version guard, the wait for publish.yml, and the merge into `latest.json`.

Neither script owns `latest.json`. Each merges its own platforms into the published feed through `scripts/feed.py`, so whichever runs second keeps the other's entries and the order the two machines run in does not matter. Entries belonging to a different version are dropped rather than carried forward, because a feed that names a new version while pointing a platform at the old artifact would offer every user on that platform an update that installs the previous build.

Building on Linux needs the Tauri system libraries: `apt install libwebkit2gtk-4.1-dev libxdo-dev libayatana-appindicator3-dev librsvg2-dev patchelf build-essential libssl-dev pkg-config`. The app itself additionally needs `bubblewrap` at runtime, which the `.deb` declares as a dependency: it is what confines each agent adapter, the way Seatbelt does on macOS.
