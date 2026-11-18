"""A part can arrive from a stranger's link, so the worker that builds it is walled in."""

import pathlib
import socket
import sys
import uuid

import pytest

from nurb import db, engine_run
from test_serve import home

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="the walls are macOS Seatbelt")

HOSTILE = '''from nurb import *
import pathlib, socket, subprocess, sqlite3

def attempt(fn):
    try:
        fn()
        return "allowed"
    except Exception as exc:
        return type(exc).__name__

@part
def hostile(width=10.0):
    tried = {{
        "write": attempt(lambda: pathlib.Path({outside!r}).write_text("owned")),
        "network": attempt(lambda: socket.create_connection(("127.0.0.1", {port}), timeout=2)),
        "program": attempt(lambda: subprocess.run(["/usr/bin/touch", {touched!r}], check=True)),
        "library": attempt(lambda: sqlite3.connect({library!r}).execute("CREATE TABLE owned (x)")),
    }}
    assert all(v != "allowed" for v in tried.values()), tried
    return Box(width, 10, 2)
'''


def test_a_part_cannot_write_reach_the_network_start_a_program_or_touch_the_library(home, tmp_path):
    outside = pathlib.Path.home() / f".nurb-sandbox-probe-{uuid.uuid4().hex}"
    touched = tmp_path / "touched"
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.settimeout(0.5)
    conn = db.connect()
    project = db.create_project(conn, "strangers")
    source = HOSTILE.format(
        outside=str(outside), port=listener.getsockname()[1], touched=str(touched), library=str(db.path())
    )
    part_id = db.create_part(conn, project, "hostile", source)
    try:
        run_id, result = engine_run.run_build(conn, part_id)
        # It built: every attempt failed, and the walls still let a part be a part.
        assert result["error"] is None, result.get("traceback") or result["error"]
        assert result["glb_bytes"]
        assert not outside.exists()
        assert not touched.exists()
        with pytest.raises(TimeoutError):
            listener.accept()
        assert "owned" not in {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
    finally:
        outside.unlink(missing_ok=True)
        listener.close()
        conn.close()
