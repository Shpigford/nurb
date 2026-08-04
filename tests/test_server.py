"""The export route is the configurator's back end: what the sliders hold, polished."""

import asyncio
import io
import json
import pathlib
from types import SimpleNamespace

import numpy as np
import pytest
import trimesh

from nurb.builder import BRIDGE_TINT
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


def test_rebuild_tints_ceilings_against_the_cards_build_direction(tmp_path):
    root = tmp_path
    (root / "parts").mkdir()
    part = root / "parts" / "thing.py"
    part.write_text(
        """from nurb import *

@part
def thing():
    return Box(6, 6, 20) + Pos(0, 0, 12) * Box(30, 30, 4)
"""
    )
    (root / "parts" / "thing.md").write_text(
        """# thing

```toml
[part]
up = [0, 0, -1]
```
"""
    )

    entry = Server(root).rebuild(part)
    scene = trimesh.load(io.BytesIO(entry["glb"]), file_type="glb")
    colors = next(iter(scene.geometry.values())).visual.vertex_colors

    assert not np.any(np.all(colors == BRIDGE_TINT, axis=1))


def test_failed_build_has_no_active_variant(tmp_path):
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    part.write_text(SCALAR_PART)
    (tmp_path / "parts" / "thing.md").write_text(SCALAR_CARD)
    server.overrides["thing"] = {"width": 0.0}

    entry = server.rebuild(part)

    assert entry["error"]
    assert entry["variant"] is None


REJECTING_PART = """from nurb import *

@part
def thing(hole=14.0):
    if hole <= 14.77:
        reject("hole must clear the 14.27mm tool: raise it above 14.77", param="hole")
    return Box(hole + 5, 20.0, 10.0)
"""


def test_rebuild_reports_a_refusal_without_a_traceback(tmp_path):
    """reject() is the part declining a configuration, not the part breaking, so the
    entry carries the message and the parameter it names and no traceback at all."""
    (tmp_path / "parts").mkdir()
    server = Server(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    part.write_text(REJECTING_PART)

    entry = server.rebuild(part)

    assert entry["error"] == "hole must clear the 14.27mm tool: raise it above 14.77"
    assert entry["refused"] == "hole"
    assert "traceback" not in entry
    # A refusal at a slider value has to be draggable back out of, so the wire
    # payload keeps both the refusal and the attempted parameter values, including
    # when there has never been a successful build to seed the viewer's panel.
    wired = server._wire(entry)
    assert wired["refused"] == "hole"
    assert wired["params"] == [
        {
            "name": "hole",
            "default": 14.0,
            "value": 14.0,
            "kind": "float",
            "doc": None,
            "family": False,
        }
    ]


def test_rebuild_marks_an_unattributed_refusal(tmp_path):
    """reject() without param still travels as a refusal; there is just no slider
    for the viewer to mark."""
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    part.write_text(REJECTING_PART.replace(', param="hole"', ""))

    entry = server.rebuild(part)

    assert entry["refused"] is True
    assert "traceback" not in entry


def test_viewer_presents_a_refusal_as_a_limit_not_a_crash():
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    # The message box turns amber, the named slider gets marked, and the sidebar
    # light says held-on-purpose rather than broken.
    assert "err.classList.toggle('refused', !!entry.refused)" in viewer
    assert "#err.refused" in viewer
    assert "function flagRefusal(e)" in viewer
    assert ".p.refused" in viewer
    assert "e.refused ? 'refused' : 'bad'" in viewer


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


def test_findings_carry_the_triangles_of_their_face(tmp_path):
    """A finding arrives with its face as a flat triangle list, so the viewer can paint
    the guilty face instead of dropping a pin near it. The subtlety guarded here:
    checks.run cleans the tessellation the rebuild left on the shape, so the check pass
    has to mesh again before any triangles exist to read."""
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    (tmp_path / "parts" / "thing.md").write_text(CARD)
    server.rebuild(part)
    walls = [f for f in server.check(part)["findings"] if f["rule"] == "min_wall"]
    assert walls, "the base card demands 10mm of a 5mm plate"
    face = walls[0]["face"]
    assert face, "the finding lost its face"
    assert len(face) % 9 == 0, "not whole triangles of three corners"


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


def test_export_names_a_variants_file_after_the_variant(tmp_path):
    """A variant is a catalog entry, so the file it exports carries the catalog name."""
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    (tmp_path / "parts" / "thing.md").write_text(CARD)
    server.overrides["thing"] = {"width": 15.0}
    server.rebuild(part)
    resp = asyncio.run(server.export("thing.stl"))
    assert resp.headers["Content-Disposition"] == 'attachment; filename="slim.stl"'
    assert json.loads(asyncio.run(server.export("thing.stl", save=True)).body) == {
        "path": str(tmp_path / "build" / "slim.stl")
    }


def test_export_can_save_into_build_and_report_the_path(tmp_path):
    """What the desktop shell asks for: a webview ignores an <a download>, so the file
    lands in build/ and the shell gets a path to reveal in Finder."""
    resp = asyncio.run(project(tmp_path).export("thing.stl", save=True))
    assert resp.status_code == 200
    saved = tmp_path / "build" / "thing.stl"
    assert json.loads(resp.body) == {"path": str(saved)}
    mesh = trimesh.load(io.BytesIO(saved.read_bytes()), file_type="stl")
    assert mesh.extents == pytest.approx([40.0, 30.0, 5.0])


def test_export_confines_a_variant_filename_to_build(tmp_path):
    server = project(tmp_path)
    escaped = tmp_path.parent / "escaped"
    server.state["thing"]["variant"] = str(escaped)

    resp = asyncio.run(server.export("thing.stl", save=True))

    saved = pathlib.Path(json.loads(resp.body)["path"])
    assert resp.status_code == 200
    assert saved.parent == tmp_path / "build"
    assert saved.name == f"{str(escaped).replace('/', '_').strip('._')}.stl"
    assert saved.is_file()
    assert not escaped.exists()


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


def test_sync_and_http_fallback_carry_the_printer_bed(tmp_path):
    server = project(tmp_path)
    (tmp_path / "printer.toml").write_text("bed = [180, 120, 180]\n")

    assert server._sync()["bed"] == [180, 120]
    response = asyncio.run(server.http(None, SimpleNamespace(path="/api/sync")))
    assert json.loads(response.body)["bed"] == [180, 120]


def test_rebuild_broadcast_carries_a_changed_printer_bed(tmp_path):
    server = project(tmp_path)
    out = sent(server)
    (tmp_path / "printer.toml").write_text("bed = [180, 120, 180]\n")

    asyncio.run(server.broadcast(server.state["thing"]))

    assert out[0]["type"] == "rebuilt"
    assert out[0]["bed"] == [180, 120]


def test_global_config_change_queues_every_part(tmp_path, monkeypatch):
    """The global printer file lives outside both directories normally watched."""
    from nurb import checks
    from nurb import server as server_mod

    config = checks.global_file()
    config.parent.mkdir(parents=True)
    config.write_text('profile = "bambu_a1_mini"\n')
    server = project(tmp_path)
    server.queue = asyncio.Queue()
    server.loop = SimpleNamespace(call_soon_threadsafe=lambda fn, arg: fn(arg))

    class FakeObserver:
        def __init__(self):
            self.scheduled = []

        def schedule(self, handler, path, recursive):
            self.scheduled.append((handler, path, recursive))

        def start(self):
            pass

    monkeypatch.setattr(server_mod, "Observer", FakeObserver)
    server.watch()
    watched = next(
        handler
        for handler, path, _ in server.observer.scheduled
        if pathlib.Path(path) == config.parent
    )
    watched.on_any_event(
        SimpleNamespace(
            is_directory=False,
            src_path=str(config.parent / "unrelated.py"),
            dest_path="",
        )
    )
    assert server.queue.empty()

    watched.on_any_event(
        SimpleNamespace(is_directory=False, src_path=str(config), dest_path="")
    )

    assert server.queue.get_nowait() == str(tmp_path / "parts" / "thing.py")


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


def test_viewer_keeps_a_deep_link_pending_until_that_part_builds():
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    assert "if (want && !msg.sources.includes(want))" in viewer
    assert "const part = current || want;" in viewer
    assert "if (!current && !want && msg.parts.length)" in viewer
    # A temporary HTTP fallback selection must not defeat the requested part
    # when the websocket reconnects or its slow build eventually lands.
    assert "if (want && parts.has(want)) current = want" in viewer
    assert "if (msg.name === want)" in viewer
    assert "want = null; wantVariant = null;" in viewer
    # Picking a variant is an explicit part selection too; a delayed deep-link
    # build must not take the canvas back afterward.
    assert "vr.onclick = () => {\n        want = null; wantVariant = null;" in viewer


def test_viewer_frames_the_first_geometry_a_page_paints():
    """A deep link's build lands as a `rebuilt`, which keeps the camera. On the
    page's first paint there is no camera to keep, and keeping the one at the
    origin painted a blank canvas over good geometry until the user reframed."""
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    assert "const keep = keepCamera && framed === name;" in viewer
    assert "} else if (!keep) {" in viewer
    assert "sectionAttach(!keep);" in viewer
    # Only a paint that actually framed a mesh may claim one: a failed build
    # returns early, so fixing the part frames it instead of keeping the origin.
    assert "framed = name;\n  lastSize = size;" in viewer


def test_sync_distinguishes_unbuilt_sources_from_unknown_deep_links(tmp_path):
    from nurb import server as server_mod

    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "waiting.py").write_text(PART, encoding="utf-8")
    server = server_mod.Server(tmp_path)

    class Connection:
        def __init__(self):
            self.sent = []

        async def send(self, payload):
            self.sent.append(json.loads(payload))

        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    connection = Connection()
    asyncio.run(server.ws(connection))

    assert connection.sent[0]["sources"] == ["waiting"]
    assert connection.sent[0]["parts"] == []


def test_viewer_updates_the_bed_outside_the_initial_socket_sync():
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    socket = viewer.split("ws.onmessage =", 1)[1]
    assert socket.index("bedUpdate(msg.bed);") < socket.index("if (msg.type === 'sync')")
    assert "fetch('/api/sync')" in viewer


def test_viewer_centers_printed_geometry_without_assembly_context():
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    paint = viewer.split("async function paint", 1)[1].split("// Takes a name", 1)[0]
    centering = paint.split("const plated =", 1)[1].split("const size =", 1)[0]
    assert "c.name !== 'context'" in centering
    assert "mesh.position.set(-at.x, -at.y, -plated.min.z)" in centering


def test_section_reaims_after_a_new_parts_camera_is_restored():
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    paint = viewer.split("async function paint", 1)[1].split("// Takes a name", 1)[0]
    assert "function sectionAttach(reaim) {\n  if (reaim) cutSign = 0;" in viewer
    assert paint.index("restoreCamera(name, box)") < paint.index("sectionAttach(!keep);")


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
