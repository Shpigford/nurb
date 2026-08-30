# nurb for Windows architecture

The Windows fork keeps the upstream nurb engine mergeable while adding a Windows-native desktop and distribution story on top.

## Layers

```
upstream nurb
      |
      v
upstream-compatible core (src/nurb/**, tests/**, examples/**, skills/**, evals/**)
      |
      v
platform abstraction (src/nurb/platform/**)
      |
      v
Windows desktop and distribution (desktop/src-tauri/**, desktop/scripts/**, .github/workflows/windows-*)
```

- **Upstream-compatible:** `src/nurb/**` core behavior, `tests/**`, `examples/**`, `skills/**`, and `evals/**`. These files stay close to upstream so routine updates merge cleanly.
- **Platform abstraction:** `src/nurb/platform/**`. Paths (`paths.py`), process launching (`process.py`), executable naming (`runtime.py`, `system.py`) live here. Windows-specific behavior should be isolated behind this layer whenever practical instead of scattering `sys.platform == "win32"` branches through the core.
- **Windows desktop/distribution:** `desktop/src-tauri/**` (Tauri shell, provisioning, process tree management, updater), `desktop/scripts/**` (cross-platform staging), and the Windows GitHub Actions.
- **Sync tooling:** `tools/upstream_sync.py` and `docs/windows/**`.

## Platform layer

`src/nurb/platform/paths.py` maps the app's directories to the OS-standard locations:

| Purpose | Windows | macOS/Linux |
| --- | --- | --- |
| User config (`config.toml`) | `%APPDATA%\nurb` | `~/Library/Application Support/nurb` / `~/.config/nurb` |
| User data | `%APPDATA%\nurb` | as above |
| Cache | `%LOCALAPPDATA%\nurb\cache` | `~/Library/Caches/nurb` / `~/.cache/nurb` |

`home_dir()` honors an explicit `HOME` even on Windows (where `pathlib.Path.home()` reads only `USERPROFILE`), so Git Bash and staged agent-skill tests share one notion of home.

## Desktop

The Tauri app (`desktop/src-tauri/`) is the primary entry point. It:

- bundles the nurb wheel, a hash-pinned uv lock, the adapter manifests, and a checksum-verified uv sidecar, staged by `desktop/scripts/stage.py`;
- provisions a managed CPython, a venv, Node LTS, and the Claude/Codex ACP adapters into `%APPDATA%\dev.alot1z.nurb.windows` on first launch;
- owns child-process lifetimes through `src-tauri/src/process.rs` (process-group creation and tree termination), the one place the platform difference is handled;
- serves the viewer, which is the same vendored three.js page that `nurb dev` and `nurb render` use, so geometry behavior is identical on Windows and Unix;
- verifies signed updates from the fork's release channel only.

The desktop app embeds the viewer in an iframe, so viewer controls reach both the app and `nurb dev` in a browser; anything about the part itself belongs in `src/nurb/viewer.html`, not the React shell.

## Runtime

The desktop build targets `x86_64-pc-windows-msvc`. The provisioned Python layout uses `Scripts/` (not `bin/`) and `node.exe` at the root of the Node archive, with `npm` invoked through `npm.cmd` on Windows. The inherited Windows `PATH` is split into entries and rebuilt rather than passed through as one string.

## SDK policy

The Windows SDK and MSVC toolchain are build prerequisites. WebView2 is the desktop web runtime used by Tauri on Windows; the NSIS installer embeds the WebView2 bootstrapper so a machine without it gets a clear install path. Windows App SDK / WinUI 3 is not a replacement for Tauri; it would be used only through a small native bridge when a Windows-only capability is genuinely useful, and no such capability is currently required.
