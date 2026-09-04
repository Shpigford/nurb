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

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

APPLE_SIGNING_IDENTITY="${APPLE_SIGNING_IDENTITY:?Set APPLE_SIGNING_IDENTITY in desktop/.env}"
APPLE_API_KEY="${APPLE_API_KEY:?Set APPLE_API_KEY (the key id) in desktop/.env}"
APPLE_API_ISSUER="${APPLE_API_ISSUER:?Set APPLE_API_ISSUER in desktop/.env}"
APPLE_API_KEY_PATH="${APPLE_API_KEY_PATH:?Set APPLE_API_KEY_PATH in desktop/.env}"
APPLE_API_KEY_PATH="${APPLE_API_KEY_PATH/#\~/$HOME}"
TAURI_SIGNING_PRIVATE_KEY="${TAURI_SIGNING_PRIVATE_KEY:?Set TAURI_SIGNING_PRIVATE_KEY (path to the updater key) in desktop/.env}"
TAURI_SIGNING_PRIVATE_KEY="${TAURI_SIGNING_PRIVATE_KEY/#\~/$HOME}"
export APPLE_SIGNING_IDENTITY APPLE_API_KEY APPLE_API_ISSUER APPLE_API_KEY_PATH TAURI_SIGNING_PRIVATE_KEY

VERSION=$(python3 -c "import json; print(json.load(open('src-tauri/tauri.conf.json'))['version'])")
PYVERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' ../pyproject.toml | head -1)
TAG="v$VERSION"
REPO="Shpigford/nurb"

if [ "$VERSION" != "$PYVERSION" ]; then
  echo "❌ tauri.conf.json says $VERSION but pyproject.toml says $PYVERSION."
  echo "   The engine and the app release as one version; bump both."
  exit 1
fi

echo "🔨 Building nurb desktop v$VERSION for Apple silicon and Intel (signed + notarized)..."
ARTIFACTS="$(mktemp -d)"
trap 'rm -rf "$ARTIFACTS"' EXIT

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

if gh release view "$TAG" --repo "$REPO" --json assets -q '.assets[].name' 2>/dev/null | grep -qx -e 'nurb-aarch64.app.tar.gz' -e 'nurb-x86_64.app.tar.gz'; then
  echo "❌ $TAG already has desktop artifacts. Bump the version to release again."
  exit 1
fi

# Keep nurb.dmg as the established Apple silicon URL. Intel Macs use a named
# companion download because GitHub release redirects cannot select an asset
# from the caller's architecture.
echo "🚀 Uploading to the $TAG release..."
gh release upload "$TAG" \
  "$ARTIFACTS/nurb.dmg" "$ARTIFACTS/nurb-intel.dmg" \
  "$ARTIFACTS/nurb-aarch64.app.tar.gz" "$ARTIFACTS/nurb-aarch64.app.tar.gz.sig" \
  "$ARTIFACTS/nurb-x86_64.app.tar.gz" "$ARTIFACTS/nurb-x86_64.app.tar.gz.sig" \
  --repo "$REPO"

echo "📡 Updating the desktop-latest feed..."
# Merged, not overwritten: the Windows CI job publishes its own entry into the
# same feed, and whichever side lands second must keep the other's platforms
# (feed.py drops them only when the published feed is an older version).
gh release download desktop-latest --repo "$REPO" --pattern latest.json \
  --output "$ARTIFACTS/existing.json" 2>/dev/null || true
python3 "$SCRIPT_DIR/feed.py" --version "$VERSION" --existing "$ARTIFACTS/existing.json" \
  --platform darwin-aarch64 "$(cat "$ARTIFACTS/nurb-aarch64.app.tar.gz.sig")" \
    "https://github.com/$REPO/releases/download/$TAG/nurb-aarch64.app.tar.gz" \
  --platform darwin-x86_64 "$(cat "$ARTIFACTS/nurb-x86_64.app.tar.gz.sig")" \
    "https://github.com/$REPO/releases/download/$TAG/nurb-x86_64.app.tar.gz" \
  > "$ARTIFACTS/latest.json"
if ! gh release view desktop-latest --repo "$REPO" >/dev/null 2>&1; then
  gh release create desktop-latest --repo "$REPO" --prerelease \
    --title "nurb desktop update feed" \
    --notes "Machine-read by installed copies of the nurb desktop app. Download the real thing from the newest release."
fi
gh release upload desktop-latest "$ARTIFACTS/latest.json" --repo "$REPO" --clobber

echo "✅ Done! Release: https://github.com/$REPO/releases/tag/$TAG"
echo "   Apple silicon: https://github.com/$REPO/releases/latest/download/nurb.dmg"
echo "   Intel: https://github.com/$REPO/releases/latest/download/nurb-intel.dmg"
echo "   Last step: run /changelog to write the site entry for v$VERSION."
