# Windows troubleshooting

## Runtime provisioning fails

Check that the bundled uv sidecar exists beside the Tauri executable and that the staged Node archive checksum matches the pinned value. Remove only the application runtime cache before retrying; never delete project directories as a troubleshooting shortcut.

## `nurb dev` reports a port conflict

The Windows socket probe uses exclusive address semantics. A real listener should be treated as busy; retry only after confirming the previous server process has exited.

## Agent or server processes remain after closing the app

The desktop process layer uses Windows process-tree termination. Inspect child processes only when diagnosing a reproducible leak; do not add feature-specific kill commands.

## Slicer not found

Use `nurb slice` with a configured printer and either put the slicer on `PATH`, install it under a standard Windows application location, or configure an explicit executable path when the application exposes that setting.

## Updates do not arrive

The updater checks the fork's `releases/latest/download/latest.json` every six hours and on launch, and the rail shows a "check for updates" button. A missing update usually means the release has no `latest.json` asset (the windows-release workflow publishes it), the app version is already newest, or the endpoint was unreachable and the failure was silent by design. Confirm the app is a release build (dev builds never check) and that `TAURI_SIGNING_PRIVATE_KEY`/`TAURI_SIGNING_PRIVATE_KEY_PASSWORD` secrets exist for the release build. The endpoint is pinned to Alot1z/nurb-windows; never point it at upstream nurb metadata.

## Paths containing spaces or Unicode

Reproduce the issue with a project directory containing both a space and a non-ASCII character. Process arguments must remain structured and path objects must not be flattened into shell strings.
