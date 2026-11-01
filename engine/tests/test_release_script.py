"""Release publication stays recoverable without replacing a live version."""

import json
import os
import pathlib
import subprocess


VERSION = "1.0.0-alpha.1"
PYVERSION = "1.0.0a1"
TAG = f"v{PYVERSION}"
FEED_URL = "https://github.com/Shpigford/nurb/releases/download/desktop-latest/latest.json"


def write_executable(path: pathlib.Path, body: str) -> None:
    path.write_text(f"#!/bin/bash\nset -euo pipefail\n{body}", encoding="utf-8")
    path.chmod(0o755)


# A stand-in for the gh CLI. GH_FEED is the published latest.json ("" for no
# feed release, __ERROR__ for a failed read), GH_RELEASE the vX.Y.Z release's
# state (missing, draft or published), GH_ASSETS whether every file is on it.
GH_STUB = """
echo "$*" >> "$GH_LOG"
if [ "$1 $2" = "repo view" ]; then echo "$GH_PERMISSION"; exit 0; fi
if [ "$1 $2" = "release download" ] && [ "$3" != desktop-latest ]; then
  # The published release's own signatures, for a feed a failed run never moved.
  while [ "$#" -gt 0 ]; do
    [ "$1" = --dir ] && { printf signature-aarch64 > "$2/nurb-aarch64.app.tar.gz.sig"; printf signature-x86_64 > "$2/nurb-x86_64.app.tar.gz.sig"; exit 0; }
    shift
  done
  exit 1
fi
if [ "$1 $2" = "release download" ]; then
  count=0
  [ ! -f "$GH_FEED_CALLS" ] || count="$(cat "$GH_FEED_CALLS")"
  count=$((count + 1))
  printf '%s' "$count" > "$GH_FEED_CALLS"
  state="$GH_FEED"
  if [ "$count" -gt 1 ] && [ "$GH_FEED_AFTER_SET" = 1 ]; then state="$GH_FEED_AFTER"; fi
  [ "$state" = __ERROR__ ] && { echo "HTTP 502: Bad Gateway" >&2; exit 1; }
  [ -n "$state" ] || { echo "release not found" >&2; exit 1; }
  while [ "$#" -gt 0 ]; do
    [ "$1" = --output ] && { printf '%s' "$state" > "$2"; exit 0; }
    shift
  done
  exit 1
fi
if [ "$1 $2" = "release view" ]; then
  if [ "$3" = desktop-latest ]; then
    [ -n "$GH_FEED" ] && exit 0
    echo "release not found" >&2; exit 1
  fi
  [ "$GH_RELEASE" = missing ] && { echo "release not found" >&2; exit 1; }
  if [[ "$*" == *isDraft* ]]; then
    [ "$GH_RELEASE" = draft ] && echo true || echo false
    exit 0
  fi
  if [ "$GH_ASSETS" = complete ]; then
    printf '%s\\n' nurb.dmg nurb-intel.dmg nurb-aarch64.app.tar.gz nurb-aarch64.app.tar.gz.sig \\
      nurb-x86_64.app.tar.gz nurb-x86_64.app.tar.gz.sig
  else
    echo nurb.dmg
  fi
  exit 0
fi
if [ "$1 $2" = "release upload" ] && [ "$3" = desktop-latest ]; then
  cp "$4" "$GH_UPLOADED_FEED"
fi
exit 0
"""


def release_fixture(
    tmp_path: pathlib.Path,
    *,
    feed: str = "",
    feed_after: str | None = None,
    release: str = "missing",
    assets: str | None = None,
    permission: str = "WRITE",
):
    repo = tmp_path / "repo"
    desktop = repo / "desktop"
    (desktop / "scripts").mkdir(parents=True)
    (desktop / "src-tauri").mkdir()
    (repo / "engine").mkdir()
    script = pathlib.Path(__file__).parents[2] / "desktop" / "scripts" / "release.sh"
    copied_script = desktop / "scripts" / "release.sh"
    copied_script.write_bytes(script.read_bytes())
    copied_script.chmod(0o755)
    (desktop / "src-tauri" / "tauri.conf.json").write_text(
        json.dumps({"version": VERSION}), encoding="utf-8"
    )
    (repo / "engine" / "pyproject.toml").write_text(f'version = "{PYVERSION}"\n', encoding="utf-8")
    (desktop / ".env").write_text(
        "APPLE_SIGNING_IDENTITY=test\nAPPLE_API_KEY=test\nAPPLE_API_ISSUER=test\n"
        "APPLE_API_KEY_PATH=/tmp/test.p8\nTAURI_SIGNING_PRIVATE_KEY=/tmp/test.key\n",
        encoding="utf-8",
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    write_executable(fake_bin / "gh", GH_STUB)
    write_executable(
        fake_bin / "npm",
        f"""
echo "$*" >> "$NPM_LOG"
target="${{@: -1}}"
arch="${{target%%-*}}"
[ "$arch" = aarch64 ] && dmg_arch=aarch64 || dmg_arch=x64
bundle="src-tauri/target/$target/release/bundle"
mkdir -p "$bundle/macos/nurb.app" "$bundle/dmg"
printf archive > "$bundle/macos/nurb.app.tar.gz"
printf "signature-$arch" > "$bundle/macos/nurb.app.tar.gz.sig"
printf dmg > "$bundle/dmg/nurb_{VERSION}_${{dmg_arch}}.dmg"
""",
    )
    for command in ("rustup", "codesign", "spctl", "xcrun"):
        write_executable(fake_bin / command, "exit 0\n")
    write_executable(fake_bin / "shlock", '[ "${RELEASE_LOCKED:-}" = 1 ] && exit 1 || exit 0\n')
    write_executable(
        fake_bin / "git",
        """
echo "$*" >> "$GIT_LOG"
if [ "$1 $2" = "rev-parse -q" ]; then exit 1; fi
if [ "$1" = status ] && [ "${GIT_DIRTY:-}" = 1 ]; then echo " M desktop/src/App.tsx"; fi
exit 0
""",
    )

    logs = {name: tmp_path / f"{name}.log" for name in ("gh", "npm", "git")}
    env = os.environ | {
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "GH_LOG": str(logs["gh"]),
        "NPM_LOG": str(logs["npm"]),
        "GIT_LOG": str(logs["git"]),
        "GH_FEED_CALLS": str(tmp_path / "feed-calls"),
        "GH_UPLOADED_FEED": str(tmp_path / "uploaded-latest.json"),
        "GH_FEED": feed,
        "GH_FEED_AFTER": feed_after or "",
        "GH_FEED_AFTER_SET": "1" if feed_after is not None else "0",
        "GH_RELEASE": release,
        "GH_ASSETS": assets or ("complete" if feed else "missing"),
        "GH_PERMISSION": permission,
        "RELEASE_LOCKED": "0",
        "TMPDIR": str(tmp_path),
    }
    return desktop, env, logs


def run(desktop, env):
    return subprocess.run(
        ["scripts/release.sh"], cwd=desktop, env=env, text=True, encoding="utf-8", capture_output=True
    )


def gh_calls(logs) -> list[str]:
    return logs["gh"].read_text(encoding="utf-8").splitlines()


def test_first_release_uploads_to_a_draft_then_publishes_and_moves_the_feed(tmp_path):
    desktop, env, logs = release_fixture(tmp_path)

    result = run(desktop, env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert logs["npm"].read_text(encoding="utf-8").count("tauri build") == 2
    assert f"push origin refs/tags/{TAG}" in logs["git"].read_text(encoding="utf-8")
    calls = gh_calls(logs)
    create = next(i for i, c in enumerate(calls) if c.startswith(f"release create {TAG} "))
    upload = next(i for i, c in enumerate(calls) if c.startswith(f"release upload {TAG} "))
    publish = next(i for i, c in enumerate(calls) if c.startswith(f"release edit {TAG} "))
    feed = next(i for i, c in enumerate(calls) if c.startswith("release upload desktop-latest "))
    assert "--draft" in calls[create] and "--verify-tag" in calls[create]
    assert create < upload < publish < feed
    assert "--draft=false" in calls[publish]
    for name in ("nurb.dmg", "nurb-intel.dmg", "nurb-aarch64.app.tar.gz.sig", "nurb-x86_64.app.tar.gz.sig"):
        assert f"/{name} " in calls[upload]

    uploaded = json.loads((tmp_path / "uploaded-latest.json").read_text(encoding="utf-8"))
    assert uploaded["version"] == VERSION
    arm = uploaded["platforms"]["darwin-aarch64"]
    assert arm["url"] == f"https://github.com/Shpigford/nurb/releases/download/{TAG}/nurb-aarch64.app.tar.gz"
    assert arm["signature"] == "signature-aarch64"
    assert uploaded["platforms"]["darwin-x86_64"]["signature"] == "signature-x86_64"


def test_draft_release_is_resumed(tmp_path):
    desktop, env, logs = release_fixture(tmp_path, release="draft")

    result = run(desktop, env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Resuming the draft" in result.stdout
    calls = gh_calls(logs)
    assert not any(c.startswith(f"release create {TAG} ") for c in calls)
    assert any(c.startswith(f"release upload {TAG} ") and "--clobber" in c for c in calls)


def test_published_version_skips_rebuild(tmp_path):
    desktop, env, logs = release_fixture(tmp_path, feed=json.dumps({"version": VERSION}), release="published")

    result = run(desktop, env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "already live" in result.stdout
    assert not logs["npm"].exists()
    assert not any(c.startswith("release upload") for c in gh_calls(logs))


def test_published_release_the_feed_missed_finishes_the_feed_without_rebuilding(tmp_path):
    desktop, env, logs = release_fixture(
        tmp_path, feed=json.dumps({"version": "0.26.0"}), release="published"
    )

    result = run(desktop, env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Finishing the feed" in result.stdout
    assert not logs["npm"].exists()
    assert not any(call.startswith(f"release upload {TAG}") for call in gh_calls(logs))
    feed = json.loads((tmp_path / "uploaded-latest.json").read_text(encoding="utf-8"))
    assert feed["version"] == VERSION
    assert feed["platforms"]["darwin-aarch64"]["signature"] == "signature-aarch64"
    assert feed["platforms"]["darwin-x86_64"]["url"].endswith(f"/download/{TAG}/nurb-x86_64.app.tar.gz")


def test_published_release_without_its_files_is_never_uploaded_twice(tmp_path):
    desktop, env, logs = release_fixture(
        tmp_path, feed=json.dumps({"version": "0.26.0"}), release="published", assets="missing"
    )

    result = run(desktop, env)

    assert result.returncode == 1
    assert "Refusing to upload twice" in result.stdout
    assert not logs["npm"].exists()
    assert not (tmp_path / "uploaded-latest.json").exists()


def test_dirty_or_unmerged_checkout_is_never_released(tmp_path):
    desktop, env, logs = release_fixture(tmp_path)

    result = run(desktop, env | {"GIT_DIRTY": "1"})

    assert result.returncode == 1
    assert "clean checkout of origin/main" in result.stdout
    assert not logs["npm"].exists()


def test_older_version_cannot_replace_current_feed(tmp_path):
    desktop, env, logs = release_fixture(tmp_path, feed=json.dumps({"version": "1.0.0"}), release="draft")

    result = run(desktop, env)

    assert result.returncode == 1
    assert "refusing to roll the feed back" in result.stdout
    assert not logs["npm"].exists()


def test_feed_read_error_aborts_instead_of_looking_unpublished(tmp_path):
    desktop, env, logs = release_fixture(tmp_path, feed="__ERROR__")

    result = run(desktop, env)

    assert result.returncode == 1
    assert "Cannot read the current desktop-latest/latest.json release state" in result.stderr
    assert not logs["npm"].exists()


def test_invalid_feed_aborts_instead_of_looking_unpublished(tmp_path):
    desktop, env, logs = release_fixture(tmp_path, feed="not-json")

    result = run(desktop, env)

    assert result.returncode == 1
    assert "not a readable release feed" in result.stderr
    assert not logs["npm"].exists()


def test_published_version_with_incomplete_artifacts_is_never_replaced(tmp_path):
    desktop, env, logs = release_fixture(
        tmp_path, feed=json.dumps({"version": VERSION}), release="published", assets="missing"
    )

    result = run(desktop, env)

    assert result.returncode == 1
    assert "immutable artifact set is incomplete or unreadable" in result.stdout
    assert not logs["npm"].exists()
    assert not any(c.startswith("release upload") for c in gh_calls(logs))


def test_feed_change_during_build_aborts_before_upload(tmp_path):
    newer = json.dumps({"version": "1.0.0-alpha.2"})
    desktop, env, logs = release_fixture(tmp_path, feed="", feed_after=newer)

    result = run(desktop, env)

    assert result.returncode == 1
    assert "published feed changed" in result.stdout
    assert logs["npm"].read_text(encoding="utf-8").count("tauri build") == 2
    assert not any(c.startswith("release upload") for c in gh_calls(logs))


def test_concurrent_release_is_rejected(tmp_path):
    desktop, env, logs = release_fixture(tmp_path)
    env["RELEASE_LOCKED"] = "1"

    result = run(desktop, env)

    assert result.returncode == 1
    assert "Another release is already running" in result.stdout
    assert not logs["npm"].exists()


def test_missing_write_access_stops_before_the_build(tmp_path):
    desktop, env, logs = release_fixture(tmp_path, permission="READ")

    result = run(desktop, env)

    assert result.returncode == 1
    assert "gh cannot write to Shpigford/nurb" in result.stdout
    assert not logs["npm"].exists()


def test_installed_apps_poll_the_feed_the_script_writes():
    """The updater endpoint and the release the script uploads latest.json to
    are one URL spelled in two files, so they must not drift apart."""
    root = pathlib.Path(__file__).parents[2]
    conf = json.loads((root / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    script = (root / "desktop" / "scripts" / "release.sh").read_text(encoding="utf-8")
    assert conf["plugins"]["updater"]["endpoints"] == [FEED_URL]
    assert 'REPO="Shpigford/nurb"' in script
    assert 'gh release upload desktop-latest "$1/latest.json"' in script
