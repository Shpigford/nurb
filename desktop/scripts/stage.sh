#!/bin/sh
# Stages what the desktop app bundles for first-launch provisioning: the nurb
# wheel built from this checkout, a fully pinned hash-locked resolution of its
# dependencies, the committed adapter manifest/lock, and the uv sidecar
# binaries for the host platform's build targets (both darwin triples on a
# Mac, the msvc triple on Windows under Git Bash). Runs before every tauri
# dev/build (wheel and Python lock are cheap and must track the checkout);
# the uv downloads are skipped once present.
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

# shasum is the mac spelling, sha256sum the coreutils one Git Bash and CI have.
checksum() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 -c - >/dev/null; else sha256sum -c - >/dev/null; fi
}

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) triples="x86_64-pc-windows-msvc" ;;
  *) triples="aarch64-apple-darwin x86_64-apple-darwin" ;;
esac

for triple in $triples; do
  case "$triple" in
    *windows*) archive="uv-$triple.zip"; binary="uv.exe"; out="$tauri/binaries/uv-$triple.exe" ;;
    *) archive="uv-$triple.tar.gz"; binary="uv"; out="$tauri/binaries/uv-$triple" ;;
  esac
  [ -e "$out" ] && continue
  echo "stage: downloading uv $UV_VERSION for $triple"
  tmp="$(mktemp -d)"
  base="https://github.com/astral-sh/uv/releases/download/$UV_VERSION"
  curl -fsSL "$base/$archive" -o "$tmp/$archive"
  curl -fsSL "$base/$archive.sha256" -o "$tmp/$archive.sha256"
  (cd "$tmp" && printf '%s  %s\n' "$(cut -d' ' -f1 "$archive.sha256")" "$archive" | checksum)
  case "$archive" in
    # Git Bash's tar is GNU tar, which cannot open zip; unzip ships with it.
    *.zip) unzip -q "$tmp/$archive" -d "$tmp" ;;
    *) tar -xzf "$tmp/$archive" -C "$tmp" ;;
  esac
  found="$(find "$tmp" -type f -name "$binary" | head -1)"
  [ -n "$found" ] || { echo "stage: uv binary not found in archive" >&2; exit 1; }
  mv "$found" "$out"
  chmod +x "$out"
  rm -rf "$tmp"
done
