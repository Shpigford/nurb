"""One release version, spelled two ways, agreed on by everything that ships."""

import pathlib
import re

import pytest


def semver_of(pep440: str) -> str:
    """PyPI speaks PEP 440 and npm speaks semver, so one release version has two
    spellings: `1.0.0a1` and `1.0.0-alpha.1`. This is the only place that mapping
    is written down, so tauri.conf.json and packages/ui/package.json cannot drift
    into their own private conventions."""
    match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:(a|b|rc)(\d+))?", pep440)
    assert match, f"not a version this release process can spell: {pep440}"
    release, kind, number = match.groups()
    if not kind:
        return release
    label = {"a": "alpha", "b": "beta", "rc": "rc"}[kind]
    return f"{release}-{label}.{number}"


def _package_version() -> str:
    import tomllib

    repo = pathlib.Path(__file__).parents[1]
    return tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


@pytest.mark.parametrize(
    "pep440,semver",
    [
        ("1.2.3", "1.2.3"),
        ("1.0.0a1", "1.0.0-alpha.1"),
        ("1.0.0b2", "1.0.0-beta.2"),
        ("1.0.0rc3", "1.0.0-rc.3"),
    ],
)
def test_semver_of_spells_a_pep440_version_for_npm(pep440, semver):
    assert semver_of(pep440) == semver


def test_desktop_app_version_is_the_package_version():
    """The desktop app and the engine release together as one version: the DMG a
    user downloads and the wheel it provisions carry the same number, and the
    updater feed advertises engine releases. A pyproject bump without the matching
    tauri.conf.json bump must go red here rather than ship a mismatched pair."""
    import json

    repo = pathlib.Path(__file__).parents[2]
    conf = json.loads((repo / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    assert conf["version"] == semver_of(_package_version())


def test_desktop_release_uses_pep440_tag_and_semver_artifact_version():
    """GitHub's engine release keeps its PEP 440 tag while Tauri and its updater metadata use SemVer, including prereleases where those spellings differ."""
    repo = pathlib.Path(__file__).parents[2]
    script = (repo / "desktop" / "scripts" / "release.sh").read_text(encoding="utf-8")
    assert 'TAG="v$PYVERSION"' in script
    assert 'if [ "$VERSION" != "$EXPECTED_VERSION" ]; then' in script
    assert '"version": "$VERSION"' in script


def test_ui_package_version_is_the_package_version():
    """@nurb/ui ships in lockstep with the wheel: the desktop app imports the
    package it was built against, so a bump that moves one and not the other
    publishes a pair that were never tested together."""
    import json

    repo = pathlib.Path(__file__).parents[2]
    pkg = json.loads((repo / "packages" / "ui" / "package.json").read_text(encoding="utf-8"))
    assert pkg["version"] == semver_of(_package_version())


def test_ui_consumers_pin_the_package_version():
    """Exact workspace pins must move with @nurb/ui or npm resolves the old
    private version from the registry instead of linking this checkout."""
    import json

    repo = pathlib.Path(__file__).parents[2]
    expected = semver_of(_package_version())
    for manifest in (repo / "desktop" / "package.json", repo / "packages" / "workbench" / "package.json"):
        package = json.loads(manifest.read_text(encoding="utf-8"))
        assert package["dependencies"]["@nurb/ui"] == expected


def test_package_lock_tracks_ui_version_and_consumer_pins():
    """A release PR must leave npm ci reproducible after every version bump."""
    import json

    repo = pathlib.Path(__file__).parents[2]
    expected = semver_of(_package_version())
    lock = json.loads((repo / "package-lock.json").read_text(encoding="utf-8"))["packages"]
    assert lock["packages/ui"]["version"] == expected
    assert lock["desktop"]["dependencies"]["@nurb/ui"] == expected
    assert lock["packages/workbench"]["dependencies"]["@nurb/ui"] == expected
