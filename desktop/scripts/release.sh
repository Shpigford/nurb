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

echo "🔨 Building nurb desktop v$VERSION (signed + notarized)..."
npm run tauri build

BUNDLE="src-tauri/target/release/bundle"
APP="$BUNDLE/macos/nurb.app"
TARGZ="$BUNDLE/macos/nurb.app.tar.gz"
DMG="$BUNDLE/dmg/nurb_${VERSION}_aarch64.dmg"

echo "🔎 Verifying the signing chain..."
codesign --verify --deep --strict "$APP"
spctl --assess --type execute "$APP"
xcrun stapler validate "$APP"

echo "🔏 Notarizing the DMG..."
xcrun notarytool submit "$DMG" \
  --key "$APPLE_API_KEY_PATH" --key-id "$APPLE_API_KEY" --issuer "$APPLE_API_ISSUER" \
  --wait
xcrun stapler staple "$DMG"

echo "📡 Writing latest.json..."
cat > "$BUNDLE/latest.json" << JSON
{
  "version": "$VERSION",
  "pub_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "platforms": {
    "darwin-aarch64": {
      "signature": "$(cat "$TARGZ.sig")",
      "url": "https://github.com/$REPO/releases/download/$TAG/nurb.app.tar.gz"
    }
  }
}
JSON

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

if gh release view "$TAG" --repo "$REPO" --json assets -q '.assets[].name' 2>/dev/null | grep -q '^nurb.app.tar.gz$'; then
  echo "❌ $TAG already has desktop artifacts. Bump the version to release again."
  exit 1
fi

# The DMG uploads under a stable name so the site can link
# releases/latest/download/nurb.dmg forever (the desktop-latest feed is a
# prerelease, which /releases/latest ignores).
cp "$DMG" "$BUNDLE/nurb.dmg"
echo "🚀 Uploading to the $TAG release..."
gh release upload "$TAG" "$BUNDLE/nurb.dmg" "$TARGZ" "$TARGZ.sig" --repo "$REPO"

echo "📡 Updating the desktop-latest feed..."
if ! gh release view desktop-latest --repo "$REPO" >/dev/null 2>&1; then
  gh release create desktop-latest --repo "$REPO" --prerelease \
    --title "nurb desktop update feed" \
    --notes "Machine-read by installed copies of the nurb desktop app. Download the real thing from the newest release."
fi
gh release upload desktop-latest "$BUNDLE/latest.json" --repo "$REPO" --clobber

echo "✅ Done! Release: https://github.com/$REPO/releases/tag/$TAG"
echo "   Latest DMG (stable URL): https://github.com/$REPO/releases/latest/download/nurb.dmg"
echo "   Last step: run /changelog to write the site entry for v$VERSION."
