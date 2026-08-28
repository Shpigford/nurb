#!/bin/sh
# Stages what the desktop app bundles for first-launch provisioning: the nurb
# wheel built from this checkout, a fully pinned hash-locked resolution of its
# dependencies, the committed adapter manifest/lock, and the uv sidecar
# binaries for the targets this host builds. Runs before every tauri dev/build (wheel
# and Python lock are cheap and must track the checkout); the uv downloads are
# skipped once present.
set -eu

here="$(cd "$(dirname "$0")" && pwd)"
tauri="$here/../src-tauri"
repo="$here/../.."
adapter_runtime="$here/../adapter-runtime"
UV_VERSION=0.12.1

mkdir -p "$tauri/resources" "$tauri/binaries"

rm -f "$tauri/resources"/nurb-*.whl
uv build --wheel --project "$repo" -o "$tauri/resources" >/dev/null 2>&1
uv pip compile "$repo/pyproject.toml" --universal --python-version 3.13 \
  --generate-hashes --no-annotate -q -o "$tauri/resources/requirements.lock"
cp "$adapter_runtime/package.json" "$tauri/resources/adapter-package.json"
cp "$adapter_runtime/package-lock.json" "$tauri/resources/adapter-package-lock.json"

# A mac release ships both arches from one machine, so it stages both. Linux
# builds one package per host arch, so it stages only its own.
case "$(uname -s)" in
  Darwin) triples="aarch64-apple-darwin x86_64-apple-darwin" ;;
  Linux) triples="$(uname -m)-unknown-linux-gnu" ;;
  *) echo "stage: unsupported host $(uname -s)" >&2; exit 1 ;;
esac

# coreutils on Linux, perl's shasum on macOS. Checking the tarball is the point,
# so a host with neither is a failure rather than a skip.
if command -v sha256sum >/dev/null 2>&1; then
  sha256_check() { sha256sum -c - >/dev/null; }
elif command -v shasum >/dev/null 2>&1; then
  sha256_check() { shasum -a 256 -c - >/dev/null; }
else
  echo "stage: no sha256sum or shasum to verify the uv download" >&2
  exit 1
fi

for triple in $triples; do
  out="$tauri/binaries/nurb-uv-$triple"
  [ -x "$out" ] && continue
  echo "stage: downloading uv $UV_VERSION for $triple"
  tmp="$(mktemp -d)"
  base="https://github.com/astral-sh/uv/releases/download/$UV_VERSION"
  curl -fsSL "$base/uv-$triple.tar.gz" -o "$tmp/uv.tar.gz"
  curl -fsSL "$base/uv-$triple.tar.gz.sha256" -o "$tmp/uv.tar.gz.sha256"
  (cd "$tmp" && printf '%s  uv.tar.gz\n' "$(cut -d' ' -f1 uv.tar.gz.sha256)" | sha256_check)
  tar -xzf "$tmp/uv.tar.gz" -C "$tmp"
  found="$(find "$tmp" -type f -name uv | head -1)"
  [ -n "$found" ] || { echo "stage: uv binary not found in tarball" >&2; exit 1; }
  mv "$found" "$out"
  chmod +x "$out"
  rm -rf "$tmp"
done
