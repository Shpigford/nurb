"""The export route is the configurator's back end: what the sliders hold, polished."""

import asyncio
import io
import json

import pytest
import trimesh

from nurb.server import Server

PART = """from nurb import *

@part
def thing(width=40.0, depth=30.0, height=5.0):
    return Box(width, depth, height)
"""


def project(tmp_path):
    (tmp_path / "parts").mkdir()
    part = tmp_path / "parts" / "thing.py"
    part.write_text(PART)
    server = Server(tmp_path)
    server.rebuild(part)
    return server


CARD = """# thing

```toml
[part]
min_wall = 10.0

[variants.slim]
note = "Half width for the narrow rail."

[variants.slim.params]
width = 15.0

[variants.slim.part]
min_wall = 1.0
```
"""

SCALAR_PART = """from nurb import *

@part
def thing(width=10.0, tall=False):
    return Box(width, 10.0, 20.0 if tall else 10.0)
"""

SCALAR_CARD = """# thing

```toml
[variants.tall.params]
tall = true

[variants.wide.params]
width = 20.0
```
"""


def test_rebuild_carries_the_cards_variants(tmp_path):
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    (tmp_path / "parts" / "thing.md").write_text(CARD)
    entry = server.rebuild(part)
    assert entry["variants"] == [
        {"name": "slim", "params": {"width": 15.0}, "note": "Half width for the narrow rail."}
    ]
    assert server._wire(entry)["variants"] == entry["variants"]


def test_rebuild_names_a_non_numeric_variant_from_its_built_values(tmp_path):
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    part.write_text(SCALAR_PART)
    (tmp_path / "parts" / "thing.md").write_text(SCALAR_CARD)
    server.rebuild(part)

    server.queue = asyncio.Queue()
    asyncio.run(
        server.command(
            json.dumps({"type": "params", "name": "thing", "values": {"tall": True}})
        )
    )
    entry = server.rebuild(part)

    assert server.overrides["thing"] == {"tall": True}
    assert entry["bbox"] == [10.0, 10.0, 20.0]
    assert entry["variant"] == "tall"


def test_failed_build_has_no_active_variant(tmp_path):
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    part.write_text(SCALAR_PART)
    (tmp_path / "parts" / "thing.md").write_text(SCALAR_CARD)
    server.overrides["thing"] = {"width": 0.0}

    entry = server.rebuild(part)

    assert entry["error"]
    assert entry["variant"] is None


def test_check_judges_a_matching_variant_by_its_own_settings(tmp_path):
    """Sliders sitting exactly on a card variant get that variant's settings, and one
    step off puts the base part's rules back."""
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    (tmp_path / "parts" / "thing.md").write_text(CARD)

    server.rebuild(part)
    rules = [f["rule"] for f in server.check(part)["findings"]]
    assert "min_wall" in rules  # the base card demands 10mm of a 5mm plate

    server.overrides["thing"] = {"width": 15.0}
    server.rebuild(part)
    rules = [f["rule"] for f in server.check(part)["findings"]]
    assert "min_wall" not in rules  # the slim variant allows 1mm

    server.overrides["thing"] = {"width": 14.0}
    server.rebuild(part)
    rules = [f["rule"] for f in server.check(part)["findings"]]
    assert "min_wall" in rules


def test_export_builds_at_the_slider_values(tmp_path):
    server = project(tmp_path)
    server.overrides["thing"] = {"width": 15.0}
    resp = asyncio.run(server.export("thing.stl"))
    assert resp.status_code == 200
    assert resp.headers["Content-Disposition"] == 'attachment; filename="thing.stl"'
    mesh = trimesh.load(io.BytesIO(resp.body), file_type="stl")
    assert mesh.extents == pytest.approx([15.0, 30.0, 5.0])
    assert mesh.is_watertight


def test_export_writes_step_too(tmp_path):
    resp = asyncio.run(project(tmp_path).export("thing.step"))
    assert resp.status_code == 200
    assert resp.body.startswith(b"ISO-10303-21")


def test_export_refuses_what_it_cannot_serve(tmp_path):
    server = project(tmp_path)
    assert asyncio.run(server.export("missing.stl")).status_code == 404
    assert asyncio.run(server.export("thing.gcode")).status_code == 404


def test_upgrade_command_only_trusts_a_uv_tool_venv(monkeypatch):
    """Recognized by where the interpreter lives: uv tool venvs sit at .../tools/nurb.

    Anything else, including this suite's own venv, gets None, because running the
    wrong upgrade on a dev checkout would replace it with PyPI.
    """
    import sys

    from nurb import server as server_mod

    assert server_mod._upgrade_command() is None
    monkeypatch.setattr(sys, "prefix", "/home/x/.local/share/uv/tools/nurb")
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv")
    assert server_mod._upgrade_command() == ["uv", "tool", "upgrade", "nurb"]
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert server_mod._upgrade_command() is None


def sent(server):
    """Capture what the server pushes to its viewers."""
    out = []

    async def record(payload):
        out.append(payload)

    server.send = record
    return out


def test_upgrade_declines_outside_a_uv_tool_install(tmp_path):
    server = Server(tmp_path)
    out = sent(server)

    async def go():
        server.queue = asyncio.Queue()  # the ws route, so the render-server gate is exercised too
        await server.command('{"type": "upgrade"}')

    asyncio.run(go())
    assert out[0]["type"] == "upgraded"
    assert "not a uv tool install" in out[0]["error"]


def test_upgrade_failure_reports_instead_of_restarting(tmp_path, monkeypatch):
    from nurb import server as server_mod

    monkeypatch.setattr(server_mod, "_upgrade_command", lambda: ["false"])
    execs = []
    monkeypatch.setattr("os.execv", lambda path, argv: execs.append(path))
    server = Server(tmp_path)
    out = sent(server)
    asyncio.run(server.upgrade())
    assert execs == []
    assert out[0]["type"] == "upgraded"
    assert out[0]["error"]


def test_upgrade_execs_the_same_argv_after_success(tmp_path, monkeypatch):
    """The restart is an exec of exactly what the user ran, flags and all."""
    import sys

    from nurb import server as server_mod

    monkeypatch.setattr(server_mod, "_upgrade_command", lambda: ["true"])
    execs = []
    monkeypatch.setattr("os.execv", lambda path, argv: execs.append((path, argv)))
    server = Server(tmp_path)
    sent(server)
    asyncio.run(server.upgrade())
    assert execs == [(sys.argv[0], sys.argv)]


def test_open_browser_fires_after_the_bind(tmp_path, monkeypatch):
    """The server opens the browser, not the CLI, because only it knows the bind landed."""
    import socket

    from nurb import server as server_mod

    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        port = held.getsockname()[1]
    (tmp_path / "parts").mkdir()
    srv = Server(tmp_path, port=port, open_browser=True)
    opened = []
    monkeypatch.setattr(server_mod, "_open_viewer", lambda url: opened.append(url))
    monkeypatch.setattr(server_mod, "_update_nudge", lambda: None)

    async def go():
        task = asyncio.create_task(srv.run())
        for _ in range(200):
            if opened:
                break
            await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(go())
    if srv.observer:
        srv.observer.stop()
    assert opened == [f"http://127.0.0.1:{port}"]


def test_open_viewer_uses_launchservices_on_macos(monkeypatch):
    """webbrowser's AppleScript path opens Safari regardless of the system default,
    so on macOS the viewer goes through /usr/bin/open instead (issue #18)."""
    import subprocess

    from nurb import server as server_mod

    ran = []
    monkeypatch.setattr(subprocess, "run", lambda argv, **kw: ran.append(argv))
    monkeypatch.setattr("sys.platform", "darwin")
    server_mod._open_viewer("http://127.0.0.1:7373")
    assert ran == [["/usr/bin/open", "http://127.0.0.1:7373"]]


def test_open_viewer_uses_webbrowser_elsewhere(monkeypatch):
    from nurb import server as server_mod

    opened = []
    monkeypatch.setattr(server_mod.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr("sys.platform", "linux")
    server_mod._open_viewer("http://127.0.0.1:7373")
    assert opened == ["http://127.0.0.1:7373"]


def test_viewer_matches_websocket_security_to_the_page():
    """An HTTPS reverse proxy needs wss; browsers block ws as mixed content."""
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    assert "location.protocol === 'https:' ? 'wss' : 'ws'" in viewer
    assert "new WebSocket(`${scheme}://${location.host}/ws`)" in viewer
    assert "new WebSocket(`ws://${location.host}/ws`)" not in viewer


# --- the skill staleness nudge ------------------------------------------------


def _install_skill(tmp_path, monkeypatch, text):
    monkeypatch.setenv("HOME", str(tmp_path))
    target = tmp_path / ".claude" / "skills" / "nurb" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text(text, encoding="utf-8")


def test_skill_nudge_names_an_older_installed_copy(tmp_path, monkeypatch, capsys):
    from nurb import server as server_mod

    _install_skill(
        tmp_path,
        monkeypatch,
        '---\nname: nurb\nmetadata:\n  version: "0.0.1"\n---\n\n# nurb\n',
    )
    server_mod._skill_nudge()
    out = capsys.readouterr().out
    assert "nurb skill 0.0.1" in out
    assert "nurb skill --sync" in out


def test_skill_nudge_treats_an_unversioned_copy_as_stale(tmp_path, monkeypatch, capsys):
    """Copies installed before versioning began have no frontmatter version at all."""
    from nurb import server as server_mod

    _install_skill(tmp_path, monkeypatch, "# nurb\n")
    server_mod._skill_nudge()
    assert "nurb skill unversioned" in capsys.readouterr().out


def test_skill_nudge_stays_quiet_on_current_and_newer_copies(tmp_path, monkeypatch, capsys):
    """A skills.sh install from GitHub can be ahead of the package between releases;
    calling it stale would invite a sync that downgrades it."""
    from nurb import __version__
    from nurb import server as server_mod

    for version in (__version__, "999.0.0"):
        _install_skill(
            tmp_path / version,
            monkeypatch,
            f'---\nmetadata:\n  version: "{version}"\n---\n\n# nurb\n',
        )
        server_mod._skill_nudge()
        assert capsys.readouterr().out == ""


def test_skill_nudge_stays_quiet_with_nothing_installed(tmp_path, monkeypatch, capsys):
    from nurb import server as server_mod

    monkeypatch.setenv("HOME", str(tmp_path))
    server_mod._skill_nudge()
    assert capsys.readouterr().out == ""
