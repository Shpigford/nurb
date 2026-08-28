#!/bin/bash
set -euo pipefail

# Releases the desktop app: signed, notarized, stapled, uploaded, updatable.
#
# The engine and the app share one version and one release. Merging the
# version bump lets publish.yml do PyPI and create the vX.Y.Z release; this
# script then builds the desktop half and uploads it to that same release,
# so it refuses to run until the tag exists. A test enforces that
# tauri.conf.json agrees with pyproject.toml, so the DMG a user downloads
# and the wheel it provisions always carry the same number.
#
# Credentials come from desktop/.env (see .env.example): a Developer ID
# certificate in the login keychain, an App Store Connect API key for
# notarization, and the updater signing key from `tauri signer generate`.
#
# What lands where: the vX.Y.Z release carries the DMG and the updater
# archive; the rolling prerelease desktop-latest carries only latest.json,
# which installed apps poll. Python releases share this repo's releases
# page, so the updater endpoint pins the rolling tag rather than trusting
# /releases/latest.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP="$SCRIPT_DIR/.."
cd "$DESKTOP"

# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

load_desktop_env

APPLE_SIGNING_IDENTITY="${APPLE_SIGNING_IDENTITY:?Set APPLE_SIGNING_IDENTITY in desktop/.env}"
APPLE_API_KEY="${APPLE_API_KEY:?Set APPLE_API_KEY (the key id) in desktop/.env}"
APPLE_API_ISSUER="${APPLE_API_ISSUER:?Set APPLE_API_ISSUER in desktop/.env}"
APPLE_API_KEY_PATH="${APPLE_API_KEY_PATH:?Set APPLE_API_KEY_PATH in desktop/.env}"
APPLE_API_KEY_PATH="${APPLE_API_KEY_PATH/#\~/$HOME}"
export APPLE_SIGNING_IDENTITY APPLE_API_KEY APPLE_API_ISSUER APPLE_API_KEY_PATH

require_updater_key
derive_version

echo "🔨 Building nurb desktop v$VERSION for Apple silicon and Intel (signed + notarized)..."
make_artifacts_dir

for target in aarch64-apple-darwin x86_64-apple-darwin; do
  arch="${target%%-*}"
  if [ "$arch" = "aarch64" ]; then
    dmg_arch="aarch64"
    dmg_name="nurb.dmg"
  else
    dmg_arch="x64"
    dmg_name="nurb-intel.dmg"
  fi

  # A cross-target build needs its Rust standard library even when the host is
  # Apple silicon. Xcode supplies the macOS SDK and linker for both slices.
  rustup target add "$target"
  npm run tauri build -- --target "$target"

  BUNDLE="src-tauri/target/$target/release/bundle"
  APP="$BUNDLE/macos/nurb.app"
  TARGZ="$BUNDLE/macos/nurb.app.tar.gz"
  DMG="$BUNDLE/dmg/nurb_${VERSION}_${dmg_arch}.dmg"
  UPDATE="nurb-${arch}.app.tar.gz"

  echo "🔎 Verifying the $arch signing chain..."
  codesign --verify --deep --strict "$APP"
  spctl --assess --type execute "$APP"
  xcrun stapler validate "$APP"

  echo "🔏 Notarizing the $arch DMG..."
  xcrun notarytool submit "$DMG" \
    --key "$APPLE_API_KEY_PATH" --key-id "$APPLE_API_KEY" --issuer "$APPLE_API_ISSUER" \
    --wait
  xcrun stapler staple "$DMG"

  # Tauri names every target's updater archive nurb.app.tar.gz. Give each one
  # a target-specific release name before the second build can overwrite it.
  cp "$TARGZ" "$ARTIFACTS/$UPDATE"
  cp "$TARGZ.sig" "$ARTIFACTS/$UPDATE.sig"
  cp "$DMG" "$ARTIFACTS/$dmg_name"
done

wait_for_tag

# Keep nurb.dmg as the established Apple silicon URL. Intel Macs use a named
# companion download because GitHub release redirects cannot select an asset
# from the caller's architecture.
echo "🚀 Uploading the macOS artifacts to the $TAG release..."
upload_release_asset_set "$TAG" "macOS desktop" "darwin-aarch64,darwin-x86_64" \
  "$ARTIFACTS/nurb.dmg" "$ARTIFACTS/nurb-intel.dmg" \
  "$ARTIFACTS/nurb-aarch64.app.tar.gz" "$ARTIFACTS/nurb-aarch64.app.tar.gz.sig" \
  "$ARTIFACTS/nurb-x86_64.app.tar.gz" "$ARTIFACTS/nurb-x86_64.app.tar.gz.sig"

DOWNLOAD="https://github.com/$REPO/releases/download/$TAG"
publish_feed \
  --platform "darwin-aarch64=$DOWNLOAD/nurb-aarch64.app.tar.gz=$ARTIFACTS/nurb-aarch64.app.tar.gz.sig" \
  --platform "darwin-x86_64=$DOWNLOAD/nurb-x86_64.app.tar.gz=$ARTIFACTS/nurb-x86_64.app.tar.gz.sig"

echo "✅ Done! Release: https://github.com/$REPO/releases/tag/$TAG"
echo "   Apple silicon: https://github.com/$REPO/releases/latest/download/nurb.dmg"
echo "   Intel: https://github.com/$REPO/releases/latest/download/nurb-intel.dmg"
echo "   Last step: run /changelog to write the site entry for v$VERSION."
