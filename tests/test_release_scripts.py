import json
import os
import pathlib
import subprocess
import textwrap


ROOT = pathlib.Path(__file__).parents[1]
DESKTOP = ROOT / "desktop"


def _fake_gh(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import os
            import pathlib
            import shutil
            import sys
            import uuid

            args = sys.argv[1:]
            state = pathlib.Path(os.environ["FAKE_GH_STATE"])
            command = args[1]
            tag = args[2]
            release = state / tag

            if command == "view":
                if "--json" in args and os.environ.get("FAKE_GH_FAIL_ASSET_QUERY"):
                    print("simulated asset query failure", file=sys.stderr)
                    sys.exit(1)
                if not release.is_dir():
                    sys.exit(1)
                if "--json" in args:
                    print("\\n".join(sorted(path.name for path in release.iterdir())))
                sys.exit(0)

            if command == "create":
                try:
                    release.mkdir()
                except FileExistsError:
                    sys.exit(1)
                sys.exit(0)

            if command == "download":
                if os.environ.get("FAKE_GH_FAIL_DOWNLOAD"):
                    sys.exit(1)
                name = args[args.index("--pattern") + 1]
                destination = pathlib.Path(args[args.index("--dir") + 1]) / name
                source = release / name
                if not source.is_file():
                    sys.exit(1)
                shutil.copy2(source, destination)
                sys.exit(0)

            if command == "delete-asset":
                name = args[3]
                try:
                    (release / name).unlink()
                except FileNotFoundError:
                    sys.exit(1)
                sys.exit(0)

            if command == "upload":
                paths = []
                for value in args[3:]:
                    if value.startswith("--"):
                        break
                    paths.append(pathlib.Path(value))
                clobber = "--clobber" in args
                if paths[0].name == "latest.json.lock" and os.environ.get("FAKE_GH_FAIL_LOCK_UPLOAD_ONCE"):
                    marker = state / ".failed-lock-upload-once"
                    if not marker.exists():
                        marker.write_text("failed")
                        sys.exit(1)
                if paths[0].name == "latest.json.lock" and os.environ.get("FAKE_GH_AMBIGUOUS_LOCK_UPLOAD_ONCE"):
                    marker = state / ".ambiguous-lock-upload-once"
                    if not marker.exists():
                        marker.write_text("failed after upload")
                        destination = release / paths[0].name
                        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
                        with os.fdopen(descriptor, "wb") as output:
                            output.write(paths[0].read_bytes())
                        sys.exit(1)
                if paths[0].name == "latest.json" and os.environ.get("FAKE_GH_FAIL_FEED_UPLOAD_ONCE"):
                    marker = state / ".failed-feed-upload-once"
                    if not marker.exists():
                        marker.write_text("failed")
                        sys.exit(1)
                limit = int(os.environ.get("FAKE_GH_UPLOAD_LIMIT", len(paths)))
                for index, source in enumerate(paths):
                    if index == limit:
                        sys.exit(1)
                    destination = release / source.name
                    if clobber:
                        temporary = release / f".{source.name}.{uuid.uuid4().hex}"
                        shutil.copy2(source, temporary)
                        os.replace(temporary, destination)
                    else:
                        try:
                            descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
                        except FileExistsError:
                            sys.exit(1)
                        with os.fdopen(descriptor, "wb") as output:
                            output.write(source.read_bytes())
                sys.exit(0)

            raise SystemExit(f"unsupported fake gh command: {args}")
            """
        )
    )
    gh.chmod(0o755)
    return bin_dir


def _environment(tmp_path, bin_dir):
    state = tmp_path / "github"
    state.mkdir()
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FAKE_GH_STATE"] = str(state)
    return state, env


def _run(script, env):
    return subprocess.run(
        ["bash", "-c", script],
        cwd=DESKTOP,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def test_feed_publication_serializes_cross_machine_merges(tmp_path):
    bin_dir = _fake_gh(tmp_path)
    state, env = _environment(tmp_path, bin_dir)
    feed_release = state / "desktop-latest"
    feed_release.mkdir()
    (feed_release / "latest.json").write_text(
        json.dumps({"version": "0.23.0", "platforms": {"darwin-aarch64": {}}})
    )
    mac_signature = tmp_path / "mac.sig"
    linux_signature = tmp_path / "linux.sig"
    mac_signature.write_text("mac-signature")
    linux_signature.write_text("linux-signature")
    prefix = "set -euo pipefail; source scripts/common.sh; REPO=test/repo; VERSION=0.24.0; make_artifacts_dir; "
    commands = [
        prefix
        + f'publish_feed --platform "darwin-aarch64=https://example.test/mac={mac_signature}"',
        prefix
        + f'publish_feed --platform "linux-x86_64=https://example.test/linux={linux_signature}"',
    ]

    processes = [
        subprocess.Popen(
            ["bash", "-c", command],
            cwd=DESKTOP,
            env=env,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for command in commands
    ]
    results = [process.communicate(timeout=20) + (process.returncode,) for process in processes]

    assert [result[2] for result in results] == [0, 0], results
    feed = json.loads((feed_release / "latest.json").read_text())
    assert feed["version"] == "0.24.0"
    assert set(feed["platforms"]) == {"darwin-aarch64", "linux-x86_64"}
    assert not (feed_release / "latest.json.lock").exists()


def test_feed_publication_fails_closed_when_asset_query_fails(tmp_path):
    bin_dir = _fake_gh(tmp_path)
    state, env = _environment(tmp_path, bin_dir)
    feed_release = state / "desktop-latest"
    feed_release.mkdir()
    original = {"version": "0.24.0", "platforms": {"darwin-aarch64": {"url": "mac"}}}
    (feed_release / "latest.json").write_text(json.dumps(original))
    signature = tmp_path / "linux.sig"
    signature.write_text("linux-signature")
    env["FAKE_GH_FAIL_DOWNLOAD"] = "1"
    env["FAKE_GH_FAIL_ASSET_QUERY"] = "1"

    result = _run(
        "set -euo pipefail; source scripts/common.sh; REPO=test/repo; VERSION=0.24.0; make_artifacts_dir; "
        + f'publish_feed --platform "linux-x86_64=https://example.test/linux={signature}"',
        env,
    )

    assert result.returncode != 0
    assert "Could not read assets" in result.stderr
    assert "Could not confirm ownership" in result.stderr
    assert json.loads((feed_release / "latest.json").read_text()) == original
    assert (feed_release / "latest.json.lock").exists()


def test_feed_lock_retries_when_failed_upload_is_followed_by_absence(tmp_path):
    bin_dir = _fake_gh(tmp_path)
    state, env = _environment(tmp_path, bin_dir)
    feed_release = state / "desktop-latest"
    feed_release.mkdir()
    signature = tmp_path / "linux.sig"
    signature.write_text("linux-signature")
    env["FAKE_GH_FAIL_LOCK_UPLOAD_ONCE"] = "1"

    result = _run(
        "set -euo pipefail; source scripts/common.sh; REPO=test/repo; VERSION=0.24.0; "
        "FEED_LOCK_ATTEMPTS=3; FEED_LOCK_SECONDS=0; make_artifacts_dir; "
        + f'publish_feed --platform "linux-x86_64=https://example.test/linux={signature}"',
        env,
    )

    assert result.returncode == 0, result.stderr
    feed = json.loads((feed_release / "latest.json").read_text())
    assert set(feed["platforms"]) == {"linux-x86_64"}
    assert not (feed_release / "latest.json.lock").exists()


def test_feed_lock_recovers_when_upload_succeeded_but_response_was_lost(tmp_path):
    bin_dir = _fake_gh(tmp_path)
    state, env = _environment(tmp_path, bin_dir)
    feed_release = state / "desktop-latest"
    feed_release.mkdir()
    signature = tmp_path / "linux.sig"
    signature.write_text("linux-signature")
    env["FAKE_GH_AMBIGUOUS_LOCK_UPLOAD_ONCE"] = "1"

    result = _run(
        "set -euo pipefail; source scripts/common.sh; REPO=test/repo; VERSION=0.24.0; "
        "FEED_LOCK_ATTEMPTS=3; FEED_LOCK_SECONDS=0; make_artifacts_dir; "
        + f'publish_feed --platform "linux-x86_64=https://example.test/linux={signature}"',
        env,
    )

    assert result.returncode == 0, result.stderr
    feed = json.loads((feed_release / "latest.json").read_text())
    assert set(feed["platforms"]) == {"linux-x86_64"}
    assert not (feed_release / "latest.json.lock").exists()


def test_feed_lock_cleanup_never_deletes_another_owners_token(tmp_path):
    bin_dir = _fake_gh(tmp_path)
    state, env = _environment(tmp_path, bin_dir)
    feed_release = state / "desktop-latest"
    feed_release.mkdir()
    lock = feed_release / "latest.json.lock"
    lock.write_text("other-owner")

    result = _run(
        "set -euo pipefail; source scripts/common.sh; REPO=test/repo; VERSION=0.24.0; "
        "make_artifacts_dir; FEED_LOCK_TOKEN=our-owner; FEED_LOCK_HELD=1",
        env,
    )

    assert result.returncode == 0
    assert "belongs to another publisher; leaving it alone" in result.stderr
    assert lock.read_text() == "other-owner"


def test_complete_assets_republish_when_feed_failed_then_refuse_after_repair(tmp_path):
    bin_dir = _fake_gh(tmp_path)
    state, env = _environment(tmp_path, bin_dir)
    release = state / "v0.24.0"
    release.mkdir()
    artifacts = []
    for name in ("nurb_x86_64.deb", "nurb_x86_64.deb.sig", "nurb-x86_64.AppImage", "nurb-x86_64.AppImage.sig"):
        path = tmp_path / name
        path.write_text(f"first:{name}")
        artifacts.append(path)
    paths = " ".join(f'"{path}"' for path in artifacts)
    command = (
        "set -euo pipefail; source scripts/common.sh; REPO=test/repo; VERSION=0.24.0; make_artifacts_dir; "
        f'upload_release_asset_set v0.24.0 linux-x86_64 "linux-x86_64,linux-x86_64-deb" {paths}; '
        f'publish_feed --platform "linux-x86_64=https://example.test/appimage={artifacts[3]}" '
        f'--platform "linux-x86_64-deb=https://example.test/deb={artifacts[1]}"'
    )
    env["FAKE_GH_FAIL_FEED_UPLOAD_ONCE"] = "1"

    failed_feed = _run(command, env)
    assert failed_feed.returncode != 0
    assert {path.name for path in release.iterdir()} == {path.name for path in artifacts}
    feed_release = state / "desktop-latest"
    assert not (feed_release / "latest.json").exists()

    for path in artifacts:
        path.write_text(f"rebuilt:{path.name}")
    repaired = _run(command, env)

    assert repaired.returncode == 0, repaired.stderr
    assert "Replacing the complete linux-x86_64 artifacts" in repaired.stdout
    for path in artifacts:
        assert (release / path.name).read_text() == f"rebuilt:{path.name}"
    feed = json.loads((feed_release / "latest.json").read_text())
    assert feed["version"] == "0.24.0"
    assert set(feed["platforms"]) == {"linux-x86_64", "linux-x86_64-deb"}

    query_failure_env = env.copy()
    query_failure_env["FAKE_GH_FAIL_DOWNLOAD"] = "1"
    query_failure_env["FAKE_GH_FAIL_ASSET_QUERY"] = "1"
    query_failure = _run(command, query_failure_env)
    assert query_failure.returncode != 0
    assert "Could not read assets" in query_failure.stderr
    for path in artifacts:
        assert (release / path.name).read_text() == f"rebuilt:{path.name}"

    refused = _run(command, env)
    assert refused.returncode != 0
    assert "already have the complete linux-x86_64 release" in refused.stdout


def test_release_asset_set_resumes_partial_upload_then_refuses_complete_set(tmp_path):
    bin_dir = _fake_gh(tmp_path)
    state, env = _environment(tmp_path, bin_dir)
    release = state / "v0.24.0"
    release.mkdir()
    artifacts = []
    for name in ("nurb_x86_64.deb", "nurb_x86_64.deb.sig", "nurb-x86_64.AppImage", "nurb-x86_64.AppImage.sig"):
        path = tmp_path / name
        path.write_text(name)
        artifacts.append(path)
    paths = " ".join(f'"{path}"' for path in artifacts)
    command = (
        "set -euo pipefail; source scripts/common.sh; REPO=test/repo; VERSION=0.24.0; make_artifacts_dir; "
        f'upload_release_asset_set v0.24.0 linux-x86_64 "linux-x86_64,linux-x86_64-deb" {paths}'
    )
    interrupted_env = env.copy()
    interrupted_env["FAKE_GH_UPLOAD_LIMIT"] = "2"

    interrupted = _run(command, interrupted_env)
    for path in artifacts:
        path.write_text(f"rebuilt:{path.name}")
    resumed = _run(command, env)
    feed_release = state / "desktop-latest"
    feed_release.mkdir()
    (feed_release / "latest.json").write_text(
        json.dumps(
            {
                "version": "0.24.0",
                "platforms": {"linux-x86_64": {}, "linux-x86_64-deb": {}},
            }
        )
    )
    duplicate = _run(command, env)

    assert interrupted.returncode != 0
    assert "Re-run this release to replace the full partial set" in interrupted.stdout
    assert resumed.returncode == 0, resumed.stderr
    assert "Replacing the partial linux-x86_64 set" in resumed.stdout
    assert {path.name for path in release.iterdir()} == {path.name for path in artifacts}
    for path in artifacts:
        assert (release / path.name).read_text() == f"rebuilt:{path.name}"
    assert duplicate.returncode != 0
    assert "already have the complete linux-x86_64 release" in duplicate.stdout
