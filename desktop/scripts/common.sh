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
FEED_LOCK_ASSET="latest.json.lock"
FEED_LOCK_ATTEMPTS=60
FEED_LOCK_SECONDS=2
FEED_LOCK_HELD=0
FEED_LOCK_TOKEN=""

# Credentials live in desktop/.env, which is not committed. See .env.example.
# CI has no .env and passes the same names in the environment, so a missing file
# is not an error here.
load_desktop_env() {
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
}

# The updater key is the one credential both platforms need. Losing it means
# shipped apps can never update again. Tauri takes either the path to the key or
# the key itself, which is what CI passes from a secret.
require_updater_key() {
  TAURI_SIGNING_PRIVATE_KEY="${TAURI_SIGNING_PRIVATE_KEY:?Set TAURI_SIGNING_PRIVATE_KEY (the updater key, or a path to it) in desktop/.env}"
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

# A scratch directory that cleans itself up. Sets ARTIFACTS. If publication
# exits between taking and releasing the remote lock, the trap gives it one
# last chance to let the other platform through.
cleanup_artifacts_dir() {
  local lock_state
  if [ "${FEED_LOCK_HELD:-0}" -eq 1 ]; then
    if feed_lock_ownership; then
      FEED_LOCK_HELD=0
      gh release delete-asset "$FEED_TAG" "$FEED_LOCK_ASSET" --repo "$REPO" --yes >/dev/null 2>&1 || \
        echo "⚠️  Could not release the $FEED_TAG feed lock. Delete $FEED_LOCK_ASSET before retrying." >&2
    else
      lock_state=$?
      FEED_LOCK_HELD=0
      if [ "$lock_state" -eq 1 ]; then
        echo "⚠️  $FEED_LOCK_ASSET belongs to another publisher; leaving it alone." >&2
      elif [ "$lock_state" -eq 2 ]; then
        echo "⚠️  Could not confirm ownership of $FEED_LOCK_ASSET; leaving it alone." >&2
      fi
    fi
  fi
  rm -rf "$ARTIFACTS"
}

make_artifacts_dir() {
  ARTIFACTS="$(mktemp -d)"
  trap cleanup_artifacts_dir EXIT
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

# Prints the assets on a release. A query failure is different from an empty
# release: callers use return code 2 to fail closed rather than overwrite or
# duplicate something they could not see.
release_asset_names() {
  local tag="$1"
  local output
  if ! output="$(gh release view "$tag" --repo "$REPO" --json assets -q '.assets[].name' 2>&1)"; then
    echo "❌ Could not read assets for $tag: $output" >&2
    return 2
  fi
  printf '%s\n' "$output"
}

release_has_asset() {
  local tag="$1"
  local name="$2"
  local assets
  if ! assets="$(release_asset_names "$tag")"; then
    return 2
  fi
  printf '%s\n' "$assets" | grep -Fqx -- "$name"
}

# Uploads one release artifact set. A complete set still refuses a second
# release. Any partial set is clobbered in full so every package and signature
# comes from the same local build.
upload_release_asset_set() {
  local tag="$1"
  local label="$2"
  local feed_platforms="$3"
  shift 3
  local total="$#"
  local assets path name after state
  local present=0
  local clobber=()
  local required_platforms=()
  IFS=',' read -r -a required_platforms <<< "$feed_platforms"

  if ! assets="$(release_asset_names "$tag")"; then
    return 1
  fi
  for path in "$@"; do
    name="${path##*/}"
    if printf '%s\n' "$assets" | grep -Fqx -- "$name"; then
      present=$((present + 1))
    fi
  done

  if [ "$present" -eq "$total" ]; then
    ensure_feed_release || return 1
    if feed_has_platforms "$VERSION" "${required_platforms[@]}"; then
      echo "❌ $tag and the update feed already have the complete $label release. Bump the version to release again."
      return 1
    else
      state=$?
      [ "$state" -eq 1 ] || return 1
    fi
    echo "↩️  Replacing the complete $label artifacts because the current feed is missing their platform keys."
    clobber=(--clobber)
  fi
  if [ "$present" -gt 0 ] && [ "$present" -lt "$total" ]; then
    echo "↩️  Replacing the partial $label set; $present of $total artifacts already exist."
    clobber=(--clobber)
  fi
  if ! gh release upload "$tag" "$@" --repo "$REPO" "${clobber[@]}"; then
    echo "❌ The $label upload stopped early. Re-run this release to replace the full partial set."
    return 1
  fi

  if ! after="$(release_asset_names "$tag")"; then
    return 1
  fi
  for path in "$@"; do
    name="${path##*/}"
    if ! printf '%s\n' "$after" | grep -Fqx -- "$name"; then
      echo "❌ $tag is still missing $name after the upload. Re-run this release."
      return 1
    fi
  done
}

ensure_feed_release() {
  if gh release view "$FEED_TAG" --repo "$REPO" >/dev/null 2>&1; then
    return
  fi
  if gh release create "$FEED_TAG" --repo "$REPO" --prerelease \
    --title "$FEED_TITLE" --notes "$FEED_NOTES"; then
    return
  fi
  # The other platform may have created it between our view and create calls.
  if ! gh release view "$FEED_TAG" --repo "$REPO" >/dev/null 2>&1; then
    echo "❌ Could not read or create the $FEED_TAG release."
    return 1
  fi
}

# Returns 0 when latest.json names this version and every requested platform,
# 1 when the feed is absent, old, or missing a key, and 2 when GitHub or JSON
# cannot be read safely.
feed_has_platforms() {
  local expected_version="$1"
  shift
  local check_dir="$ARTIFACTS/release-feed-check"
  local check_file="$check_dir/latest.json"
  local download_error state
  mkdir -p "$check_dir"
  rm -f "$check_file"

  if ! download_error="$(gh release download "$FEED_TAG" --repo "$REPO" --pattern latest.json --dir "$check_dir" 2>&1)"; then
    if release_has_asset "$FEED_TAG" latest.json; then
      echo "❌ latest.json exists but could not be downloaded: $download_error" >&2
      return 2
    else
      state=$?
      [ "$state" -eq 1 ] && return 1
      return 2
    fi
  fi

  if python3 - "$check_file" "$expected_version" "$@" <<'PY'
import json
import pathlib
import sys

try:
    feed = json.loads(pathlib.Path(sys.argv[1]).read_text())
except (OSError, json.JSONDecodeError) as exc:
    print(f"latest.json is not readable: {exc}", file=sys.stderr)
    raise SystemExit(2)
platforms = feed.get("platforms")
if not isinstance(platforms, dict):
    print("latest.json has no platforms object", file=sys.stderr)
    raise SystemExit(2)
if feed.get("version") != sys.argv[2] or any(name not in platforms for name in sys.argv[3:]):
    raise SystemExit(1)
PY
  then
    return 0
  else
    state=$?
    [ "$state" -eq 1 ] && return 1
    return 2
  fi
}

# Downloads the current lock token. Return 3 means confirmed absence; return 2
# means GitHub could not answer safely.
read_remote_feed_lock() {
  local check_dir="$ARTIFACTS/feed-lock-check"
  local check_file="$check_dir/$FEED_LOCK_ASSET"
  local download_error state
  mkdir -p "$check_dir"
  rm -f "$check_file"

  if download_error="$(gh release download "$FEED_TAG" --repo "$REPO" --pattern "$FEED_LOCK_ASSET" --dir "$check_dir" 2>&1)"; then
    if [ ! -f "$check_file" ]; then
      echo "❌ GitHub reported a lock download but wrote no $FEED_LOCK_ASSET." >&2
      return 2
    fi
    cat "$check_file"
    return
  fi
  if release_has_asset "$FEED_TAG" "$FEED_LOCK_ASSET"; then
    echo "❌ $FEED_LOCK_ASSET exists but could not be downloaded: $download_error" >&2
    return 2
  else
    state=$?
    [ "$state" -eq 1 ] && return 3
    return 2
  fi
}

# Returns 0 only when the published token is ours, 1 for another owner, 2 for
# an API failure, and 3 when the lock is confirmed absent.
feed_lock_ownership() {
  local remote state
  if remote="$(read_remote_feed_lock)"; then
    [ "$remote" = "$FEED_LOCK_TOKEN" ]
    return
  else
    state=$?
    return "$state"
  fi
}

# A fixed release asset is an atomic cross-machine lock: GitHub accepts only
# one upload with this name. Its UUID proves ownership when an upload succeeds
# remotely but the response is lost locally.
acquire_feed_lock() {
  local lock_file="$ARTIFACTS/$FEED_LOCK_ASSET"
  local attempt upload_error state
  FEED_LOCK_TOKEN="$(python3 -c 'import uuid; print(uuid.uuid4())')"
  printf '%s\n' "$FEED_LOCK_TOKEN" > "$lock_file"

  for attempt in $(seq 1 "$FEED_LOCK_ATTEMPTS"); do
    if upload_error="$(gh release upload "$FEED_TAG" "$lock_file" --repo "$REPO" 2>&1)"; then
      FEED_LOCK_HELD=1
      return
    fi
    if feed_lock_ownership; then
      FEED_LOCK_HELD=1
      return
    else
      state=$?
    fi
    case "$state" in
      # Another owner still holds it, or the holder released it before our
      # check. Both cases race back to acquisition.
      1 | 3) ;;
      *) return 1 ;;
    esac
    if [ "$attempt" -eq "$FEED_LOCK_ATTEMPTS" ]; then
      echo "❌ Timed out waiting for the other platform to publish $FEED_TAG."
      echo "   Last lock upload error: $upload_error" >&2
      echo "   If no release is running, delete $FEED_LOCK_ASSET from $FEED_TAG and retry."
      return 1
    fi
    sleep "$FEED_LOCK_SECONDS"
  done
}

release_feed_lock() {
  local state
  if feed_lock_ownership; then
    # Do not let the EXIT trap retry this deletion. If GitHub deletes the asset
    # but the response is lost, a retry could delete the next owner's lock.
    FEED_LOCK_HELD=0
    if ! gh release delete-asset "$FEED_TAG" "$FEED_LOCK_ASSET" --repo "$REPO" --yes; then
      echo "❌ Published latest.json but could not release $FEED_LOCK_ASSET. Delete it before the next release." >&2
      return 1
    fi
    return
  fi
  state=$?
  FEED_LOCK_HELD=0
  case "$state" in
    1) echo "❌ $FEED_LOCK_ASSET now belongs to another publisher; refusing to delete it." >&2 ;;
    3) echo "❌ $FEED_LOCK_ASSET disappeared before publication finished." >&2 ;;
    *) echo "❌ Could not confirm ownership of $FEED_LOCK_ASSET; refusing to delete it." >&2 ;;
  esac
  return 1
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
  local state
  echo "📡 Merging into latest.json..."
  ensure_feed_release
  acquire_feed_lock

  # A download that failed and a feed that does not exist yet look identical
  # from the exit status, and reading a network blip as "nothing published yet"
  # would drop the other platform on the --clobber upload below. So when the
  # download fails, ask the release what assets it has before believing it.
  if ! gh release download "$FEED_TAG" --repo "$REPO" --pattern latest.json \
    --dir "$ARTIFACTS" >/dev/null 2>&1; then
    if release_has_asset "$FEED_TAG" latest.json; then
      echo "❌ $FEED_TAG has a latest.json but it would not download."
      echo "   Publishing now would drop the other platform's entries. Retry when the network is back."
      return 1
    else
      state=$?
      [ "$state" -eq 1 ] || return 1
    fi
  fi

  python3 scripts/feed.py \
    --version "$VERSION" \
    --current "$ARTIFACTS/latest.json" \
    --out "$ARTIFACTS/latest.json" \
    "$@"
  gh release upload "$FEED_TAG" "$ARTIFACTS/latest.json" --repo "$REPO" --clobber
  release_feed_lock
}
