#!/bin/bash
set -euo pipefail

# Releases the desktop app: signed, notarized, stapled, uploaded, updatable.
#
# The engine and the app share one version and one release. A test enforces
# that tauri.conf.json agrees with pyproject.toml, so the DMG a user downloads
# and the wheel it provisions always carry the same number. Run this after the
# version bump is merged; it tags the commit it built from.
#
# Credentials come from desktop/.env (see .env.example): a Developer ID
# certificate in the login keychain, an App Store Connect API key for
# notarization, and the updater signing key from `tauri signer generate`.
# GitHub access comes from `gh auth login`.
#
# What lands where: the vX.Y.Z release carries the DMGs and the updater
# archives; the rolling prerelease desktop-latest carries only latest.json,
# which installed apps poll. The updater endpoint pins that rolling tag
# rather than /releases/latest, so the feed moves only when this script says.
# The release stays a draft until every file is on it, so the site's
# /releases/latest/download links never point at a release without its DMGs.

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
# A shipped app must carry Satoshi, so the build fails rather than falling back.
export NURB_REQUIRE_FONTS=1

REPO="Shpigford/nurb"
command -v gh >/dev/null || { echo "❌ The gh CLI uploads to GitHub Releases. brew install gh"; exit 1; }
command -v shlock >/dev/null || { echo "❌ shlock is required to serialize releases on this Mac."; exit 1; }
# Prove the login and the write access now, not after a twenty-minute build.
case "$(gh repo view "$REPO" --json viewerPermission -q .viewerPermission 2>/dev/null)" in
  ADMIN|MAINTAIN|WRITE) ;;
  *) echo "❌ gh cannot write to $REPO. Run gh auth login with an account that can."; exit 1 ;;
esac

# Signing only runs on this Mac, so one machine-local lock closes the long
# build/notarization race between two workspaces releasing at once.
# shlock removes a stale lock whose PID is no longer alive.
RELEASE_LOCK="${TMPDIR:-/tmp}/nurb-release.lock"
if ! shlock -p "$$" -f "$RELEASE_LOCK"; then
  echo "❌ Another release is already running."
  exit 1
fi
ARTIFACTS=""
cleanup() {
  [ -z "$ARTIFACTS" ] || rm -rf "$ARTIFACTS"
  rm -f "$RELEASE_LOCK"
}
trap cleanup EXIT

VERSION=$(python3 -c "import json; print(json.load(open('src-tauri/tauri.conf.json'))['version'])")
PYVERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' ../engine/pyproject.toml | head -1)
EXPECTED_VERSION=$(python3 - "$PYVERSION" <<'PY'
import re
import sys

match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:(a|b|rc)(\d+))?", sys.argv[1])
if not match:
    raise SystemExit(f"unsupported PEP 440 release version: {sys.argv[1]}")
release, kind, number = match.groups()
if kind:
    label = {"a": "alpha", "b": "beta", "rc": "rc"}[kind]
    release = f"{release}-{label}.{number}"
print(release)
PY
)
TAG="v$PYVERSION"
FILES=(nurb.dmg nurb-intel.dmg nurb-aarch64.app.tar.gz nurb-aarch64.app.tar.gz.sig nurb-x86_64.app.tar.gz nurb-x86_64.app.tar.gz.sig)

# The tag goes on HEAD and the build reads the working tree, so both must be main.
git fetch -q origin main
if [ -n "$(git status --porcelain)" ] || [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
  echo "❌ Release from a clean checkout of origin/main; this one is dirty or on another commit."
  exit 1
fi

if [ "$VERSION" != "$EXPECTED_VERSION" ]; then
  echo "❌ tauri.conf.json says $VERSION but pyproject.toml says $PYVERSION ($EXPECTED_VERSION in SemVer)."
  echo "   The engine and the app release as one version; bump both."
  exit 1
fi

published_version() {
  local feed_file out version
  feed_file="$(mktemp)"

  if ! out=$(gh release download desktop-latest --repo "$REPO" --pattern latest.json \
    --output "$feed_file" --clobber 2>&1); then
    rm -f "$feed_file"
    # No feed release, or a feed release without the file, is a first release.
    # Any other failure means the read failed: never mistake an unknown
    # current release for an empty one.
    case "$out" in
      *"release not found"*|*"no assets match"*) return 0 ;;
    esac
    echo "❌ Cannot read the current desktop-latest/latest.json release state." >&2
    return 1
  fi
  if ! version=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["version"])' "$feed_file" 2>/dev/null); then
    rm -f "$feed_file"
    echo "❌ The published latest.json is not a readable release feed." >&2
    return 1
  fi
  rm -f "$feed_file"
  printf '%s\n' "$version"
}

# Prints missing, draft or published for the vX.Y.Z release.
release_state() {
  local out
  if out=$(gh release view "$TAG" --repo "$REPO" --json isDraft -q .isDraft 2>&1); then
    [ "$out" = true ] && echo draft || echo published
    return 0
  fi
  case "$out" in
    *"release not found"*) echo missing; return 0 ;;
  esac
  echo "❌ Cannot read the $TAG release." >&2
  return 1
}

artifacts_complete() {
  local assets file
  assets=$(gh release view "$TAG" --repo "$REPO" --json assets -q '.assets[].name') || return 1
  for file in "${FILES[@]}"; do
    grep -qx "$file" <<<"$assets" || return 1
  done
}

# The feed for $TAG, from the directory holding both updater signatures.
write_feed() {
cat > "$1/latest.json" << JSON
{
  "version": "$VERSION",
  "notes": "nurb $VERSION. What changed: https://nurb.dev/changelog",
  "pub_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "platforms": {
    "darwin-aarch64": {
      "signature": "$(cat "$1/nurb-aarch64.app.tar.gz.sig")",
      "url": "https://github.com/$REPO/releases/download/$TAG/nurb-aarch64.app.tar.gz"
    },
    "darwin-x86_64": {
      "signature": "$(cat "$1/nurb-x86_64.app.tar.gz.sig")",
      "url": "https://github.com/$REPO/releases/download/$TAG/nurb-x86_64.app.tar.gz"
    }
  }
}
JSON
python3 -c "import json, sys; json.load(open(sys.argv[1]))" "$1/latest.json"
}

upload_feed() {
  if ! gh release view desktop-latest --repo "$REPO" >/dev/null 2>&1; then
    gh release create desktop-latest --repo "$REPO" --prerelease \
      --title "nurb desktop update feed" \
      --notes "Machine-read by installed copies of the nurb desktop app. Download the real thing from the newest release."
  fi
  gh release upload desktop-latest "$1/latest.json" --repo "$REPO" --clobber
}

publish_tag() {
  if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
    if [ "$(git rev-list -n 1 "$TAG")" != "$(git rev-parse HEAD)" ]; then
      echo "❌ $TAG points at a different commit; refusing to move a release tag."
      exit 1
    fi
  else
    echo "🏷  Tagging $TAG..."
    git tag -a "$TAG" -m "nurb $VERSION"
  fi
  git push origin "refs/tags/$TAG"
}

PUBLISHED_VERSION="$(published_version)"
if [ "$PUBLISHED_VERSION" = "$VERSION" ]; then
  if ! artifacts_complete; then
    echo "❌ nurb $VERSION is already published, but its immutable artifact set is incomplete or unreadable."
    echo "   Refusing to replace files under the live version."
    exit 1
  fi
  echo "✅ nurb $VERSION is already live. Nothing to do."
  exit 0
fi

if [ -n "$PUBLISHED_VERSION" ]; then
  ORDER=$(python3 - "$VERSION" "$PUBLISHED_VERSION" <<'PY'
import re
import sys

def order(version):
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)\.(\d+))?", version)
    if not match:
        raise SystemExit(f"unsupported SemVer release version: {version}")
    major, minor, patch, kind, number = match.groups()
    prerelease = {"alpha": 0, "beta": 1, "rc": 2, None: 3}[kind]
    return (int(major), int(minor), int(patch), prerelease, int(number or 0))

print((order(sys.argv[1]) > order(sys.argv[2])) - (order(sys.argv[1]) < order(sys.argv[2])))
PY
  )
  if [ "$ORDER" -lt 0 ]; then
    echo "❌ $PUBLISHED_VERSION is already live; refusing to roll the feed back to $VERSION."
    exit 1
  fi
fi

RELEASE_STATE="$(release_state)"
if [ "$RELEASE_STATE" = published ]; then
  # A run that died between publishing the release and moving the feed. The
  # files are final, so finish the feed from the published signatures rather
  # than building and uploading again.
  if ! artifacts_complete; then
    echo "❌ $TAG is published without its full artifact set. Refusing to upload twice."
    exit 1
  fi
  echo "↻ $TAG is published but the feed does not offer it. Finishing the feed."
  ARTIFACTS="$(mktemp -d)"
  gh release download "$TAG" --repo "$REPO" --pattern '*.sig' --dir "$ARTIFACTS"
  write_feed "$ARTIFACTS"
  upload_feed "$ARTIFACTS"
  echo "✅ Feed: https://github.com/$REPO/releases/download/desktop-latest/latest.json"
  exit 0
fi
if [ "$RELEASE_STATE" = draft ]; then
  echo "↻ Resuming the draft $TAG release."
fi

echo "🔨 Building nurb desktop v$VERSION for Apple silicon and Intel (signed + notarized)..."
ARTIFACTS="$(mktemp -d)"

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

echo "📡 Writing latest.json..."
write_feed "$ARTIFACTS"

# The signing build takes long enough for external state to change. The local
# lock serializes this Mac; this second read also refuses a manual/remote
# publication that happened while the build was running.
LATEST_VERSION="$(published_version)"
if [ "$LATEST_VERSION" != "$PUBLISHED_VERSION" ]; then
  echo "❌ The published feed changed from ${PUBLISHED_VERSION:-<none>} to ${LATEST_VERSION:-<none>} during the build."
  echo "   Refusing to overwrite newer release state."
  exit 1
fi
# A failed read stops here: set -e applies to an assignment, not to a test.
RELEASE_STATE="$(release_state)"
if [ "$RELEASE_STATE" = published ]; then
  echo "❌ $TAG was published during the build. Refusing to upload twice."
  exit 1
fi

# The tag records the commit the release came from. A tag left by an earlier
# attempt is pushed again, but never moved.
publish_tag

if [ "$RELEASE_STATE" = missing ]; then
  gh release create "$TAG" --repo "$REPO" --verify-tag --draft \
    --title "nurb $VERSION" --notes "What changed: https://nurb.dev/changelog#v$VERSION"
fi

# Keep nurb.dmg as the established Apple silicon URL. Intel Macs use a named
# companion download because GitHub release redirects cannot select an asset
# from the caller's architecture. --clobber only ever replaces files on the
# unpublished draft, which is how a partial upload resumes.
echo "🚀 Uploading to the $TAG release..."
gh release upload "$TAG" \
  "$ARTIFACTS/nurb.dmg" "$ARTIFACTS/nurb-intel.dmg" \
  "$ARTIFACTS/nurb-aarch64.app.tar.gz" "$ARTIFACTS/nurb-aarch64.app.tar.gz.sig" \
  "$ARTIFACTS/nurb-x86_64.app.tar.gz" "$ARTIFACTS/nurb-x86_64.app.tar.gz.sig" \
  --repo "$REPO" --clobber
gh release edit "$TAG" --repo "$REPO" --draft=false --latest

echo "📡 Updating the desktop-latest feed..."
upload_feed "$ARTIFACTS"

echo "✅ Done! Release: https://github.com/$REPO/releases/tag/$TAG"
echo "   Apple silicon: https://github.com/$REPO/releases/latest/download/nurb.dmg"
echo "   Intel: https://github.com/$REPO/releases/latest/download/nurb-intel.dmg"
echo "   Feed: https://github.com/$REPO/releases/download/desktop-latest/latest.json"
echo "   Last step: run /changelog to write the site entry for $TAG."
