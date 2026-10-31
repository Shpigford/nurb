#!/bin/sh
# Rebuilds the debug bundle from this checkout and relaunches it, replacing the
# instance a previous run started. The app keeps its own data home so it never
# touches an installed release. Pass --no-build to relaunch what is there.
set -eu

here="$(cd "$(dirname "$0")" && pwd)"
desktop="$here/.."
app="$desktop/src-tauri/target/debug/bundle/macos/nurb.app"
bin="$app/Contents/MacOS/nurb"
home="${NURB_DESKTOP_DATA:-$HOME/.nurb-dev}"
log="$home/app.log"

if [ "${1:-}" != "--no-build" ]; then
  # tauri exits non-zero at the updater signing step (no TAURI_SIGNING_PRIVATE_KEY)
  # after the .app is already bundled, so judge the build by a fresh binary instead.
  stamp="$(mktemp)"
  (cd "$desktop" && npx tauri build --debug --bundles app) || true
  [ -x "$bin" ] && [ "$bin" -nt "$stamp" ] || { rm -f "$stamp"; echo "dev: build failed, no fresh bundle at $app" >&2; exit 1; }
  rm -f "$stamp"
fi
[ -x "$bin" ] || { echo "dev: no bundle at $app" >&2; exit 1; }

# Only the instance from this bundle path; an installed nurb.app stays up.
pkill -f "^$bin" 2>/dev/null && sleep 1 || true

mkdir -p "$home"
NURB_DESKTOP_DATA="$home" nohup "$bin" >> "$log" 2>&1 &
echo "dev: launched $app"
echo "dev: data home $home, log $log"
