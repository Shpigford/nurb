#!/bin/bash
set -euo pipefail

# Releases the Linux desktop packages: a .deb, an AppImage, and the updater
# archive installed copies poll for.
#
# The companion to release.sh, which does the same for macOS. They cannot be
# one script because Tauri links against the host's system webview, so each
# platform builds on its own machine. Both upload into the vX.Y.Z release that
# publish.yml creates from the merged version bump, and both merge their own
# half into one latest.json through feed.py rather than overwriting it.
#
# Ordering does not matter. Run this before or after the Mac; whichever goes
# second picks up the other's entries. What does matter is that both run for
# the same version, because feed.py drops entries from an older one.
#
# Credentials: only the updater signing key, from `tauri signer generate`.
# There is no Linux equivalent of notarization, so unlike the Mac script this
# needs no certificate and no App Store Connect key.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP="$SCRIPT_DIR/.."
cd "$DESKTOP"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

TAURI_SIGNING_PRIVATE_KEY="${TAURI_SIGNING_PRIVATE_KEY:?Set TAURI_SIGNING_PRIVATE_KEY (path to the updater key) in desktop/.env}"
TAURI_SIGNING_PRIVATE_KEY="${TAURI_SIGNING_PRIVATE_KEY/#\~/$HOME}"
export TAURI_SIGNING_PRIVATE_KEY

VERSION=$(python3 -c "import json; print(json.load(open('src-tauri/tauri.conf.json'))['version'])")
PYVERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' ../pyproject.toml | head -1)
TAG="v$VERSION"
REPO="Shpigford/nurb"

if [ "$VERSION" != "$PYVERSION" ]; then
  echo "❌ tauri.conf.json says $VERSION but pyproject.toml says $PYVERSION."
  echo "   The engine and the app release as one version; bump both."
  exit 1
fi

# bubblewrap is what confines every agent adapter, and the .deb declares it as a
# dependency. Building without it installed still produces a package, but it
# means this machine has never run the sandboxed path it is shipping.
if ! command -v bwrap >/dev/null 2>&1; then
  echo "⚠️  bubblewrap is not installed here, so the sandbox has not been exercised."
  echo "   apt install bubblewrap, then run the Rust tests before releasing."
fi

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) DEB_ARCH="amd64"; FEED_ARCH="x86_64" ;;
  aarch64) DEB_ARCH="arm64"; FEED_ARCH="aarch64" ;;
  *) echo "❌ unsupported architecture $ARCH"; exit 1 ;;
esac

echo "🔨 Building nurb desktop v$VERSION for linux-$FEED_ARCH..."
ARTIFACTS="$(mktemp -d)"
trap 'rm -rf "$ARTIFACTS"' EXIT

npm run tauri build

BUNDLE="src-tauri/target/release/bundle"
DEB="$BUNDLE/deb/nurb_${VERSION}_${DEB_ARCH}.deb"
APPIMAGE="$BUNDLE/appimage/nurb_${VERSION}_${DEB_ARCH}.AppImage"
UPDATE_SRC="$APPIMAGE.tar.gz"

for file in "$DEB" "$APPIMAGE" "$UPDATE_SRC" "$UPDATE_SRC.sig"; do
  if [ ! -f "$file" ]; then
    echo "❌ the build did not produce $file"
    exit 1
  fi
done

# The published names carry the architecture, because a GitHub release redirect
# cannot pick an asset from the caller's machine.
DEB_NAME="nurb_${FEED_ARCH}.deb"
APPIMAGE_NAME="nurb-${FEED_ARCH}.AppImage"
UPDATE_NAME="nurb-${FEED_ARCH}.AppImage.tar.gz"
cp "$DEB" "$ARTIFACTS/$DEB_NAME"
cp "$APPIMAGE" "$ARTIFACTS/$APPIMAGE_NAME"
cp "$UPDATE_SRC" "$ARTIFACTS/$UPDATE_NAME"
cp "$UPDATE_SRC.sig" "$ARTIFACTS/$UPDATE_NAME.sig"

echo "🔎 Checking the package declares its dependencies..."
dpkg-deb --field "$ARTIFACTS/$DEB_NAME" Depends

# The build runs before this wait on purpose: merge the bump and run this
# script immediately, and the desktop build overlaps publish.yml's run.
echo "⏳ Waiting for publish.yml to create the $TAG release..."
for attempt in $(seq 1 90); do
  gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1 && break
  if [ "$attempt" -eq 90 ]; then
    echo "❌ $TAG never appeared. Is the version bump merged? Did publish.yml fail?"
    exit 1
  fi
  sleep 10
done

if gh release view "$TAG" --repo "$REPO" --json assets -q '.assets[].name' 2>/dev/null | grep -qx "$UPDATE_NAME"; then
  echo "❌ $TAG already has linux-$FEED_ARCH artifacts. Bump the version to release again."
  exit 1
fi

echo "🚀 Uploading to the $TAG release..."
gh release upload "$TAG" \
  "$ARTIFACTS/$DEB_NAME" "$ARTIFACTS/$APPIMAGE_NAME" \
  "$ARTIFACTS/$UPDATE_NAME" "$ARTIFACTS/$UPDATE_NAME.sig" \
  --repo "$REPO"

echo "📡 Merging linux-$FEED_ARCH into latest.json..."
if ! gh release view desktop-latest --repo "$REPO" >/dev/null 2>&1; then
  gh release create desktop-latest --repo "$REPO" --prerelease \
    --title "nurb desktop update feed" \
    --notes "Machine-read by installed copies of the nurb desktop app. Download the real thing from the newest release."
fi
# Whatever the Mac already published, if anything: feed.py keeps it when the
# version matches and drops it when it does not.
gh release download desktop-latest --repo "$REPO" --pattern latest.json \
  --dir "$ARTIFACTS" >/dev/null 2>&1 || true
python3 scripts/feed.py \
  --version "$VERSION" \
  --current "$ARTIFACTS/latest.json" \
  --out "$ARTIFACTS/latest.json" \
  --platform "linux-$FEED_ARCH=https://github.com/$REPO/releases/download/$TAG/$UPDATE_NAME=$ARTIFACTS/$UPDATE_NAME.sig"
gh release upload desktop-latest "$ARTIFACTS/latest.json" --repo "$REPO" --clobber

echo "✅ Done! Release: https://github.com/$REPO/releases/tag/$TAG"
echo "   Debian/Ubuntu: https://github.com/$REPO/releases/latest/download/$DEB_NAME"
echo "   AppImage: https://github.com/$REPO/releases/latest/download/$APPIMAGE_NAME"
echo "   If the Mac half has not run yet, latest.json carries Linux only until it does."
