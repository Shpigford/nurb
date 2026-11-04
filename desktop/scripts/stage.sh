#!/bin/sh
# Stages what the desktop app bundles for first-launch provisioning: the nurb
# wheel built from this checkout, its dependencies as pinned by uv.lock, the
# committed adapter manifest/lock, and the uv sidecar binaries for both darwin
# targets. Runs before every tauri dev/build (wheel and Python lock are cheap and
# must track the checkout); the uv downloads are skipped once present.
#
# The lock's bytes decide whether an installed app keeps its environment, so they
# depend on uv.lock and nothing else: no header naming this checkout's path, and
# no fresh resolve that picks up whatever is newest on the day of the build.
set -eu

here="$(cd "$(dirname "$0")" && pwd)"
tauri="$here/../src-tauri"
repo="$here/../../engine"
adapter_runtime="$here/../adapter-runtime"
UV_VERSION=0.12.1

mkdir -p "$tauri/resources" "$tauri/binaries"

rm -f "$tauri/resources"/nurb-*.whl
uv build --wheel --project "$repo" -o "$tauri/resources" >/dev/null 2>&1
uv export --project "$repo" --locked --no-dev --no-emit-project --no-header \
  --no-annotate --format requirements-txt -q -o "$tauri/resources/requirements.lock"
cp "$adapter_runtime/package.json" "$tauri/resources/adapter-package.json"
cp "$adapter_runtime/package-lock.json" "$tauri/resources/adapter-package-lock.json"

for triple in aarch64-apple-darwin x86_64-apple-darwin; do
  out="$tauri/binaries/uv-$triple"
  [ -x "$out" ] && continue
  echo "stage: downloading uv $UV_VERSION for $triple"
  tmp="$(mktemp -d)"
  base="https://github.com/astral-sh/uv/releases/download/$UV_VERSION"
  curl -fsSL "$base/uv-$triple.tar.gz" -o "$tmp/uv.tar.gz"
  curl -fsSL "$base/uv-$triple.tar.gz.sha256" -o "$tmp/uv.tar.gz.sha256"
  (cd "$tmp" && printf '%s  uv.tar.gz\n' "$(cut -d' ' -f1 uv.tar.gz.sha256)" | shasum -a 256 -c - >/dev/null)
  tar -xzf "$tmp/uv.tar.gz" -C "$tmp"
  found="$(find "$tmp" -type f -name uv | head -1)"
  [ -n "$found" ] || { echo "stage: uv binary not found in tarball" >&2; exit 1; }
  mv "$found" "$out"
  chmod +x "$out"
  rm -rf "$tmp"
done
