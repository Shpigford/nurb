#!/bin/bash
set -euo pipefail

# Releases the Linux desktop packages: a .deb and an AppImage, each signed so
# installed copies can update themselves to it.
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

# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

load_desktop_env
require_updater_key
derive_version

# bubblewrap is what confines every agent adapter, and the .deb declares it as a
# dependency. Building without it installed still produces a package, but it
# means this machine has never run the sandboxed path it is shipping.
if ! command -v bwrap >/dev/null 2>&1; then
  echo "⚠️  bubblewrap is not installed here, so the sandbox has not been exercised."
  echo "   apt install bubblewrap, then run the Rust tests before releasing."
fi

# tauri-bundler names the two packages with different words for the same
# machine: the .deb follows Debian (arm64) and the AppImage follows uname
# (aarch64). They agree only on x86_64, which is why getting this wrong is
# invisible until someone releases for ARM.
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) DEB_ARCH="amd64"; APPIMAGE_ARCH="amd64"; FEED_ARCH="x86_64" ;;
  aarch64) DEB_ARCH="arm64"; APPIMAGE_ARCH="aarch64"; FEED_ARCH="aarch64" ;;
  *) echo "❌ unsupported architecture $ARCH"; exit 1 ;;
esac

echo "🔨 Building nurb desktop v$VERSION for linux-$FEED_ARCH..."
make_artifacts_dir

npm run tauri build

# Unlike macOS, Linux has no updater tarball. Both packages are self-contained
# updater artifacts, so the bundler signs each one where it sits and the feed
# points at the package itself.
BUNDLE="src-tauri/target/release/bundle"
DEB="$BUNDLE/deb/nurb_${VERSION}_${DEB_ARCH}.deb"
APPIMAGE="$BUNDLE/appimage/nurb_${VERSION}_${APPIMAGE_ARCH}.AppImage"

for file in "$DEB" "$DEB.sig" "$APPIMAGE" "$APPIMAGE.sig"; do
  if [ ! -f "$file" ]; then
    echo "❌ the build did not produce $file"
    exit 1
  fi
done

# The published names carry the architecture, because a GitHub release redirect
# cannot pick an asset from the caller's machine.
DEB_NAME="nurb_${FEED_ARCH}.deb"
APPIMAGE_NAME="nurb-${FEED_ARCH}.AppImage"
cp "$DEB" "$ARTIFACTS/$DEB_NAME"
cp "$DEB.sig" "$ARTIFACTS/$DEB_NAME.sig"
cp "$APPIMAGE" "$ARTIFACTS/$APPIMAGE_NAME"
cp "$APPIMAGE.sig" "$ARTIFACTS/$APPIMAGE_NAME.sig"

echo "🔎 Checking the package declares its dependencies..."
dpkg-deb --field "$ARTIFACTS/$DEB_NAME" Depends

wait_for_tag

if gh release view "$TAG" --repo "$REPO" --json assets -q '.assets[].name' 2>/dev/null | grep -qx "$APPIMAGE_NAME"; then
  echo "❌ $TAG already has linux-$FEED_ARCH artifacts. Bump the version to release again."
  exit 1
fi

echo "🚀 Uploading to the $TAG release..."
gh release upload "$TAG" \
  "$ARTIFACTS/$DEB_NAME" "$ARTIFACTS/$DEB_NAME.sig" \
  "$ARTIFACTS/$APPIMAGE_NAME" "$ARTIFACTS/$APPIMAGE_NAME.sig" \
  --repo "$REPO"

# Two entries, because the updater asks for its own package format first. A
# copy installed from the .deb looks for linux-<arch>-deb and would otherwise
# fall through to the AppImage entry, download something dpkg cannot install,
# and never update again.
DOWNLOAD="https://github.com/$REPO/releases/download/$TAG"
publish_feed \
  --platform "linux-$FEED_ARCH=$DOWNLOAD/$APPIMAGE_NAME=$ARTIFACTS/$APPIMAGE_NAME.sig" \
  --platform "linux-$FEED_ARCH-deb=$DOWNLOAD/$DEB_NAME=$ARTIFACTS/$DEB_NAME.sig"

echo "✅ Done! Release: https://github.com/$REPO/releases/tag/$TAG"
echo "   Debian/Ubuntu: https://github.com/$REPO/releases/latest/download/$DEB_NAME"
echo "   AppImage: https://github.com/$REPO/releases/latest/download/$APPIMAGE_NAME"
echo "   If the Mac half has not run yet, latest.json carries Linux only until it does."
