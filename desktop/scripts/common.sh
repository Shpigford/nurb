#!/bin/bash
# What release.sh and release-linux.sh both need. Sourced, never run.
#
# The two scripts run on different machines because Tauri links against the
# host's system webview, but everything around the build is the same: the same
# repo, the same version guard, the same wait for publish.yml, and the same
# merge into one update feed. Keeping that here means the two halves cannot
# drift into disagreeing about which release they are uploading to.

REPO="Shpigford/nurb"
FEED_TAG="desktop-latest"
FEED_TITLE="nurb desktop update feed"
FEED_NOTES="Machine-read by installed copies of the nurb desktop app. Download the real thing from the newest release."
TAG_WAIT_ATTEMPTS=90
TAG_WAIT_SECONDS=10

# Credentials live in desktop/.env, which is not committed. See .env.example.
load_desktop_env() {
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
}

# The updater key is the one credential both platforms need. Losing it means
# shipped apps can never update again.
require_updater_key() {
  TAURI_SIGNING_PRIVATE_KEY="${TAURI_SIGNING_PRIVATE_KEY:?Set TAURI_SIGNING_PRIVATE_KEY (path to the updater key) in desktop/.env}"
  TAURI_SIGNING_PRIVATE_KEY="${TAURI_SIGNING_PRIVATE_KEY/#\~/$HOME}"
  export TAURI_SIGNING_PRIVATE_KEY
}

# Sets VERSION and TAG, and refuses to go on if the engine and the app disagree.
derive_version() {
  VERSION=$(python3 -c "import json; print(json.load(open('src-tauri/tauri.conf.json'))['version'])")
  PYVERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' ../pyproject.toml | head -1)
  TAG="v$VERSION"

  if [ "$VERSION" != "$PYVERSION" ]; then
    echo "❌ tauri.conf.json says $VERSION but pyproject.toml says $PYVERSION."
    echo "   The engine and the app release as one version; bump both."
    exit 1
  fi
}

# A scratch directory that cleans itself up. Sets ARTIFACTS.
make_artifacts_dir() {
  ARTIFACTS="$(mktemp -d)"
  trap 'rm -rf "$ARTIFACTS"' EXIT
}

# The build runs before this wait on purpose: merge the bump and run the release
# script immediately, and the desktop build overlaps publish.yml's run.
wait_for_tag() {
  echo "⏳ Waiting for publish.yml to create the $TAG release..."
  for attempt in $(seq 1 "$TAG_WAIT_ATTEMPTS"); do
    gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1 && break
    if [ "$attempt" -eq "$TAG_WAIT_ATTEMPTS" ]; then
      echo "❌ $TAG never appeared. Is the version bump merged? Did publish.yml fail?"
      exit 1
    fi
    sleep "$TAG_WAIT_SECONDS"
  done
}

# Merges the platforms named in "$@" (feed.py --platform arguments) into the
# published latest.json and uploads the result.
#
# Neither script owns the feed. The other machine publishes its own half into
# this same file, so this reads what is there and merges rather than
# overwriting. feed.py keeps the other platform's entries when the version
# matches and drops them when it does not, which is what stops a one-sided
# release from offering the other platform an update that installs the
# previous build.
publish_feed() {
  echo "📡 Merging into latest.json..."
  if ! gh release view "$FEED_TAG" --repo "$REPO" >/dev/null 2>&1; then
    gh release create "$FEED_TAG" --repo "$REPO" --prerelease \
      --title "$FEED_TITLE" --notes "$FEED_NOTES"
  fi

  # A download that failed and a feed that does not exist yet look identical
  # from the exit status, and reading a network blip as "nothing published yet"
  # would drop the other platform on the --clobber upload below. So when the
  # download fails, ask the release what assets it has before believing it.
  if ! gh release download "$FEED_TAG" --repo "$REPO" --pattern latest.json \
    --dir "$ARTIFACTS" >/dev/null 2>&1; then
    if gh release view "$FEED_TAG" --repo "$REPO" --json assets -q '.assets[].name' 2>/dev/null | grep -qx 'latest.json'; then
      echo "❌ $FEED_TAG has a latest.json but it would not download."
      echo "   Publishing now would drop the other platform's entries. Retry when the network is back."
      exit 1
    fi
  fi

  python3 scripts/feed.py \
    --version "$VERSION" \
    --current "$ARTIFACTS/latest.json" \
    --out "$ARTIFACTS/latest.json" \
    "$@"
  gh release upload "$FEED_TAG" "$ARTIFACTS/latest.json" --repo "$REPO" --clobber
}
