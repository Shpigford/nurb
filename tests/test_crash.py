"""A fault inside the CAD kernel ends as a build error, not a dead interpreter.

Issue #247: a polish on a united body took OCCT down with a segfault, `nurb build` died
with signal 11, and every `nurb dev` restart walked into the same build and raised
another macOS crash dialog. The fault here is the same kernel call the report named,
reached directly: an adaptor with no curve dereferences null in `D0`.
"""

import json
import os
import pathlib
import queue
import socket
import subprocess
import sys
import threading
import time
import urllib.request

import pytest
from websockets.sync.client import connect

from nurb import cli
from nurb import server as server_mod
from nurb.server import Server

NURB = pathlib.Path(sys.executable).with_name("nurb")

CRASHING = '''
from nurb import *
from OCP.Geom2dAdaptor import Geom2dAdaptor_Curve
from OCP.gp import gp_Pnt2d


@part
def bracket(width=40.0, draft=False):
    body = Box(width, 20, 5)
    if draft:
        return body
    Geom2dAdaptor_Curve().D0(0.0, gp_Pnt2d())
    return body
'''

PLATE = '''
from nurb import *


@part
def plate(width=30.0):
    return Box(width, 30, 3)
'''


def _project(root):
    (root / "parts").mkdir()
    (root / "parts" / "bracket.py").write_text(CRASHING, encoding="utf-8")
    (root / "parts" / "plate.py").write_text(PLATE, encoding="utf-8")
    return root


def test_build_reports_a_kernel_fault_as_an_error(tmp_path):
    _project(tmp_path)
    done = subprocess.run(
        [NURB, "build", "bracket"], cwd=tmp_path, capture_output=True, text=True, timeout=120
    )
    # 1, the way any failed command exits; never a signal death (-11, or 139 in a shell).
    assert done.returncode == 1
    assert "the CAD kernel crashed (segmentation fault) building bracket" in done.stderr
    assert "at parts/bracket.py:12" in done.stderr
    assert "Polish the simple solids before uniting them" in done.stderr


def _free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _lines(proc):
    out = queue.Queue()
    threading.Thread(target=lambda: [out.put(l) for l in proc.stdout], daemon=True).start()
    return out


def _until(lines, needle, deadline):
    seen = []
    while time.monotonic() < deadline:
        try:
            line = lines.get(timeout=1)
        except queue.Empty:
            continue
        seen.append(line)
        if needle in line:
            return seen
    raise AssertionError(f"never saw {needle!r} in:\n{''.join(seen)}")


@pytest.mark.parametrize("launcher", [[NURB], [sys.executable, "-m", "nurb.cli"]])
def test_dev_restarts_itself_and_marks_the_part_instead_of_crashing_again(tmp_path, launcher):
    _project(tmp_path)
    port = _free_port()
    proc = subprocess.Popen(
        [*launcher, "dev", "--port", str(port)],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 180
        lines = _lines(proc)
        _until(lines, "restarting the server", deadline)
        # The same process comes back on the same port, says what happened to the part
        # in one status line, and builds the rest of the project.
        seen = _until(lines, "plate:", deadline)
        text = "".join(seen)
        assert "bracket: the CAD kernel crashed (segmentation fault) building bracket" in text
        assert text.count("restarting the server") == 0, "the marked part was built again"
        assert proc.poll() is None
        with socket.create_connection(("127.0.0.1", port), timeout=5):
            pass
    finally:
        proc.terminate()
        proc.wait(timeout=30)


def test_rebuild_skips_a_marked_part_until_its_inputs_change(tmp_path, monkeypatch):
    (tmp_path / "parts").mkdir()
    part = tmp_path / "parts" / "thing.py"
    part.write_text(
        "from nurb import *\nimport pathlib\n\n@part\ndef thing(width=10.0):\n"
        "    pathlib.Path(__file__).with_name('built').touch()\n    return Box(width, 10, 10)\n",
        encoding="utf-8",
    )
    key = Server(tmp_path)._crash_key(part, None, False)
    marker = {"path": str(part), "key": key, "error": "the CAD kernel crashed", "traceback": "detail"}
    resumed = {
        "port": 7373, "draft": False, "overrides": {}, "crashed": {str(part): marker},
    }
    monkeypatch.setenv(server_mod.CRASHED, json.dumps(resumed))
    server = Server(tmp_path)
    assert server_mod.CRASHED not in os.environ, "the marker is consumed, not inherited again"

    entry = server.rebuild(part)
    assert entry["error"] == "the CAD kernel crashed"
    assert entry["traceback"] == "detail"
    assert entry["glb"] is None
    assert not (tmp_path / "parts" / "built").exists(), "the marked part was built"
    # The sliders still come from the file, so another configuration can be tried.
    assert [(p["name"], p["value"]) for p in entry["params"]] == [("width", 10.0)]

    server.overrides["thing"] = {"width": 12.0}
    entry = server.rebuild(part)
    assert entry["error"] is None
    assert (tmp_path / "parts" / "built").exists()
    assert server.crashed == {}


def _parts(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/parts", timeout=5) as response:
        return {entry["name"]: entry for entry in json.load(response)}


def _params(port, name, values):
    with connect(f"ws://127.0.0.1:{port}/ws", origin=f"http://127.0.0.1:{port}") as ws:
        ws.recv(timeout=5)
        ws.send(json.dumps({"type": "params", "name": name, "values": values}))


def test_second_kernel_fault_recovers_with_all_slider_values(tmp_path):
    _project(tmp_path)
    port = _free_port()
    proc = subprocess.Popen(
        [NURB, "dev", "--port", str(port)], cwd=tmp_path,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        lines = _lines(proc)
        deadline = time.monotonic() + 120
        _until(lines, "plate:", deadline)
        _params(port, "plate", {"width": 35.0})
        _until(lines, "plate:", deadline)
        _params(port, "bracket", {"width": 45.0})
        _until(lines, "restarting the server", deadline)
        _until(lines, "plate:", deadline)
        entries = _parts(port)
        bracket = entries["bracket"]
        assert "CAD kernel crashed" in bracket["error"]
        assert bracket["params"][0]["value"] == 45.0
        assert entries["plate"]["params"][0]["value"] == 35.0
        assert proc.poll() is None
    finally:
        proc.terminate()
        proc.wait(timeout=30)


def test_two_crashing_parts_remain_marked_across_restarts(tmp_path):
    _project(tmp_path)
    (tmp_path / "parts" / "clamp.py").write_text(
        CRASHING.replace("def bracket(", "def clamp("), encoding="utf-8"
    )
    port = _free_port()
    proc = subprocess.Popen(
        [NURB, "dev", "--port", str(port)], cwd=tmp_path,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        seen = _until(_lines(proc), "plate:", time.monotonic() + 120)
        assert "".join(seen).count("restarting the server") == 2
        entries = _parts(port)
        assert "CAD kernel crashed" in entries["bracket"]["error"]
        assert "CAD kernel crashed" in entries["clamp"]["error"]
        assert entries["plate"]["error"] is None
        assert proc.poll() is None
    finally:
        proc.terminate()
        proc.wait(timeout=30)


def test_dev_restores_resolved_port_and_draft_without_opening_another_tab(tmp_path, monkeypatch):
    _project(tmp_path)
    port = _free_port()
    restored = {
        "port": port, "draft": True, "overrides": {"plate": {"width": 35.0}},
        "crashed": {},
    }
    monkeypatch.setenv(server_mod.CRASHED, json.dumps(restored))
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    asked = []
    actual_pick = cli._pick_port

    def pick(asked_port, root):
        asked.append(asked_port)
        return actual_pick(asked_port, root)

    async def run(server):
        assert server.port == port
        assert server.draft is True
        assert server.overrides == restored["overrides"]
        assert server.open_browser is False

    monkeypatch.setattr(cli, "_pick_port", pick)
    monkeypatch.setattr(Server, "run", run)
    cli.main(["dev", "--open"])
    assert asked == [port]


def test_auto_port_restart_keeps_existing_viewer_and_opens_only_once(tmp_path):
    _project(tmp_path)
    (tmp_path / "parts" / "bracket.py").write_text(
        CRASHING.replace("if draft:", "if draft or width != 45:"), encoding="utf-8"
    )
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", 0))
    blocker.listen()
    first = blocker.getsockname()[1]
    # Stub only the external browser opener; exercise real CLI port selection, server startup and crash recovery.
    script = (
        "import sys; from nurb import cli, server; "
        "cli.DEFAULT_PORT = int(sys.argv[1]); "
        "server._open_viewer = lambda url: print('BROWSER OPEN ' + url, flush=True); "
        "cli.main(['dev', '--open'])"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", script, str(first)], cwd=tmp_path,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        lines = _lines(proc)
        deadline = time.monotonic() + 120
        seen = _until(lines, "plate:", deadline)
        opened = [line for line in seen if line.startswith("BROWSER OPEN ")]
        assert len(opened) == 1
        port = int(opened[0].strip().rsplit(":", 1)[1])
        assert port != first
        blocker.close()
        _params(port, "bracket", {"width": 45.0})
        seen = _until(lines, "restarting the server", deadline)
        seen += _until(lines, "plate:", deadline)
        assert not any(line.startswith("BROWSER OPEN ") for line in seen)
        assert "CAD kernel crashed" in _parts(port)["bracket"]["error"]
        assert proc.poll() is None
    finally:
        blocker.close()
        proc.terminate()
        proc.wait(timeout=30)
