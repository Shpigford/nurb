"""The export route is the configurator's back end: what the sliders hold, polished."""

import asyncio
import io
import json
import pathlib
import threading
import time
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


# --- what the print costs -----------------------------------------------------
# The route the viewer's "print time" button calls. Nothing in CI has a slicer, so
# the two answers exercised here are the ones that come back without running one:
# the question that gets a picker, and the shape identity that decides how long an
# answer is allowed to stay on screen.


def test_slice_asks_which_printer_rather_than_refusing(tmp_path, monkeypatch):
    """A machine that was never chosen is a question, and the viewer needs the list
    to ask it with. Reporting `no printer chosen` and stopping is the dead end this
    whole surface exists to avoid.

    The slicer is stubbed present because a missing one outranks a missing printer,
    and this test is about the second question. Without the stub it passes on a
    developer's Mac, where a slicer is installed, and asserts the wrong branch in CI,
    where none is.
    """
    from nurb import checks, slicing

    monkeypatch.setattr(slicing, "app", lambda *a, **k: pathlib.Path("/Applications/Orca"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
    said = json.loads(asyncio.run(project(tmp_path).slice("thing")).body)
    assert said["kind"] == "choose"
    assert "error" not in said
    assert said["profiles"] == sorted(checks.profiles())


def test_choosing_a_printer_replies_only_to_the_viewer_that_asked(tmp_path):
    """Another open viewer must not treat this acknowledgement as its own request and
    immediately slice whichever part it happens to show."""
    server = project(tmp_path)
    server.queue = asyncio.Queue()

    class Client:
        def __init__(self):
            self.messages = []

        async def send(self, raw):
            self.messages.append(json.loads(raw))

    asking, other = Client(), Client()
    server.clients = {asking, other}
    asyncio.run(
        server.command(
            json.dumps({"type": "printer", "profile": "bambu_a1_mini"}),
            asking,
        )
    )

    assert asking.messages == [
        {"type": "printer", "profile": "bambu_a1_mini", "bed": [180.0, 180.0]}
    ]
    assert other.messages == []


def test_slice_says_what_is_missing_before_it_needs_a_printer(tmp_path, monkeypatch):
    """No slicer outranks no printer: naming a machine would not help."""
    from nurb import slicing

    monkeypatch.setattr(slicing, "app", lambda *a, **k: None)
    said = json.loads(asyncio.run(project(tmp_path).slice("thing")).body)
    assert said["kind"] == "slicer"
    assert "OrcaSlicer" in said["error"]
    # No machine list, because no choice on it would help: nothing here can be picked
    # into existence, and the viewer keys its calm no-retry state off exactly this.
    assert "profiles" not in said


def test_a_machine_the_slicer_does_not_carry_offers_the_others(tmp_path, monkeypatch):
    """A fault the user can act on. `nurb slice` prints the neighbouring machines and
    stops; the viewer has to be able to offer them, or the row is a wall with a button
    on it that fails identically every time."""
    from nurb import checks, slicing

    monkeypatch.setattr(slicing, "app", lambda *a, **k: "/Applications/OrcaSlicer")
    monkeypatch.setattr(slicing, "vendors", lambda exe: pathlib.Path(tmp_path))
    monkeypatch.setattr(
        slicing, "machine", lambda *a, **k: (_ for _ in ()).throw(slicing.Unavailable("no H2C here"))
    )
    (tmp_path / "printer.toml").write_text('profile = "bambu_a1_mini"\n')

    said = json.loads(asyncio.run(project(tmp_path).slice("thing")).body)

    assert said["kind"] == "profile"
    assert said["error"] == "no H2C here"
    assert said["profiles"] == sorted(checks.profiles())


def test_a_model_the_slicer_refuses_does_not_offer_a_printer_picker(tmp_path, monkeypatch):
    """Once machine and presets resolved, a refusal belongs to this model or slicer
    run. Changing the printer is not the generic repair for it."""
    from nurb import slicing

    server = project(tmp_path)
    (tmp_path / "printer.toml").write_text('profile = "bambu_a1_mini"\n')
    monkeypatch.setattr(slicing, "app", lambda *a, **k: "/Applications/BambuStudio")
    monkeypatch.setattr(slicing, "vendors", lambda exe: tmp_path)
    monkeypatch.setattr(slicing, "machine", lambda *a, **k: tmp_path / "machine.json")
    monkeypatch.setattr(
        slicing,
        "profiles_for",
        lambda *a, **k: (tmp_path / "process.json", tmp_path / "filament.json"),
    )

    async def refused(*args):
        raise slicing.Unavailable("the slicer refused this model: exit code 156")

    monkeypatch.setattr(server, "_sliced", refused)

    said = json.loads(asyncio.run(server.slice("thing")).body)

    assert said == {
        "kind": "slice",
        "error": "the slicer refused this model: exit code 156",
    }


def test_the_viewer_keeps_a_missing_slicer_out_of_the_fault_colour():
    """Nothing is broken and nothing the user does in this window fixes it, so the row
    stays calm, names the two apps, and points at the file button instead of offering a
    retry that fails identically."""
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    branch = viewer[viewer.index("if (ask.kind === 'slicer') {") :]
    branch = branch[: branch.index("return")] + branch[branch.index("return") : branch.index("\n  }")]
    assert '"ask line"' in branch  # calm, not the fault colour
    assert "stl still works" in branch
    assert "class=\"go\"" not in branch  # no retry that cannot succeed


def test_slice_refuses_a_part_it_does_not_have(tmp_path):
    assert asyncio.run(project(tmp_path).slice("missing")).status_code == 404


def test_slice_route_requires_the_socket_token(tmp_path, monkeypatch):
    """A page on another origin can GET localhost, but it cannot learn and attach the
    secret the viewer receives through its origin-checked websocket."""
    server = project(tmp_path)
    called = []

    async def sliced(name):
        called.append(name)
        return server._json(200, {"name": name})

    monkeypatch.setattr(server, "slice", sliced)
    denied = asyncio.run(
        server.http(None, SimpleNamespace(path="/api/slice/thing", headers={}))
    )
    allowed = asyncio.run(
        server.http(
            None,
            SimpleNamespace(
                path="/api/slice/thing",
                headers={"X-Nurb-Token": server.http_token},
            ),
        )
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert called == ["thing"]
    assert "request_token" not in server._sync()
    assert server._sync(include_token=True)["request_token"] == server.http_token
    viewer = pathlib.Path(__file__).parents[1] / "src" / "nurb" / "viewer.html"
    assert "'X-Nurb-Token': requestToken" in viewer.read_text(encoding="utf-8")


def test_identical_geometry_keeps_its_shape_id(tmp_path):
    """The rule an estimate hangs on. A rebuild that changed nothing, which is what a
    printer.toml edit causes, must not read as a new shape, or the answer the user
    just paid a slicer for deletes itself."""
    server = project(tmp_path)
    part = tmp_path / "parts" / "thing.py"
    first = server.state["thing"]["shape_id"]
    assert first == server.rebuild(part)["shape_id"]

    server.overrides["thing"] = {"width": 15.0}
    assert server.rebuild(part)["shape_id"] != first


def test_an_assembly_estimate_keeps_repeated_instances_and_their_overrides(
    tmp_path, monkeypatch
):
    """A bill of materials counts physical instances, not unique source files, and a
    configured use must not silently rebuild from the leaf's defaults."""
    from nurb import slicing

    (tmp_path / "parts").mkdir()
    thing = tmp_path / "parts" / "thing.py"
    thing.write_text(PART)
    inner = tmp_path / "parts" / "inner.py"
    inner.write_text(
        """from nurb import *

@assembly
def inner():
    return use("thing", width=12.0), Pos(50, 0, 0) * use("thing", width=12.0)
"""
    )
    rig = tmp_path / "parts" / "rig.py"
    rig.write_text(
        """from nurb import *

@assembly
def rig():
    return use("inner"), Pos(100, 0, 0) * use("thing", width=20.0)
"""
    )
    server = Server(tmp_path)
    server.rebuild(thing)
    server.rebuild(inner)
    server.rebuild(rig)
    server.overrides["thing"] = {"width": 99.0}  # irrelevant to the assembly's uses

    printable = [(path.stem, overrides) for path, overrides in server._printable("rig")]
    assert printable == [
        ("thing", {"width": 12.0}),
        ("thing", {"width": 12.0}),
        ("thing", {"width": 20.0}),
    ]

    built = []
    monkeypatch.setattr(
        server,
        "_solid",
        lambda path, overrides, target: built.append((path.stem, overrides)) or target,
    )
    monkeypatch.setattr(
        slicing,
        "run",
        lambda model, target, *args: ((100, 2.0), target),
    )

    totals = asyncio.run(server._sliced("rig", "machine", "process", "filament", "exe"))

    assert totals == (300, 6.0, 3)
    assert built == [("thing", {"width": 12.0}), ("thing", {"width": 20.0})]


def test_an_assembly_that_places_nothing_has_nothing_to_print(tmp_path):
    from nurb.assembly import Scene

    server = project(tmp_path)
    server.state["rig"] = {
        "name": "rig",
        "shape": SimpleNamespace(_nurb_scene=Scene()),
        "joints": [],
        "uses": [],
    }
    with pytest.raises(Exception, match="nothing to print"):
        server._printable("rig")


def test_concurrent_estimates_do_not_run_the_slicer_together(tmp_path, monkeypatch):
    """Two viewer tabs can ask for the same part together; their slicers must not share
    and delete the adapter's per-target staging files."""
    from nurb import slicing

    server = project(tmp_path)
    active = high_water = 0
    guard = threading.Lock()

    monkeypatch.setattr(server, "_solid", lambda path, overrides, target: target)

    def run(model, target, *args):
        nonlocal active, high_water
        with guard:
            active += 1
            high_water = max(high_water, active)
        time.sleep(0.03)
        with guard:
            active -= 1
        return (10, 1.0), target

    monkeypatch.setattr(slicing, "run", run)

    async def both():
        args = ("thing", "machine", "process", "filament", "exe")
        return await asyncio.gather(server._sliced(*args), server._sliced(*args))

    assert asyncio.run(both()) == [(10, 1.0, 1), (10, 1.0, 1)]
    assert high_water == 1


def test_the_viewer_carries_a_print_estimate_and_never_a_stale_one():
    """The surface itself. A command with no control in the viewer does not exist for
    the person who downloaded the app, and an estimate that outlived its geometry is
    worse than none, so the card and the shape check are both pinned here."""
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    assert 'id="print"' in viewer
    assert "/api/slice/" in viewer
    # Shown only while the part on screen still hashes to what was sliced.
    assert "said.shape_id === e.shape_id" in viewer
    # The unnamed machine gets a picker, not a sentence about a file.
    assert 'id="printerpick"' in viewer
    assert "type: 'printer', profile: event.target.value" in viewer


def test_the_print_estimate_is_its_own_row_and_not_a_sixth_toolbar_button():
    """Where it lives is the feature, and two earlier cuts got it wrong. A sixth button
    in the pill ran the toolbar into the checks panel at the width the desktop app
    gives the viewer, and putting the answer in the bottom-left readout meant the user
    who pressed the button never saw it arrive."""
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    tools = viewer[viewer.index('<div id="tools">') : viewer.index('<div id="hud">')]
    pill = tools[tools.index('<div class="pill">') : tools.index("</div>")]
    # In the toolbar column, beside the pill, never inside it.
    assert '<div id="print"></div>' in tools
    assert "print" not in pill
    # The click and the number it produces are the same element.
    assert "printbox.onclick" in viewer
    assert "printbox.innerHTML" in viewer
    # And the answer is not smuggled back into the corner readout.
    hud = viewer[viewer.index("function hud(e) {") : viewer.index("// ---- parameters ----")]
    assert "printed" not in hud


def test_the_print_row_cannot_reach_the_checks_panel():
    """Both are overlays anchored to opposite top corners, and this row grows leftward.
    With only the viewport to stop it, it slid under the checks card on a narrow viewer.
    The two widths have to leave no room to meet."""
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    assert "max-width: 46%" in viewer  # checks
    assert "max-width: 54%" in viewer  # the print row
