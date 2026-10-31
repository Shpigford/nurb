"""What a build run has to survive, and what it has to remember.

Three invariants carried over from the v1 watcher, re-asserted against the v2 engine.
A kernel fault used to take the whole watcher down with it (issue #247); now the
spawned worker contains it, so the containment is asserted twice: once in process, and
once through a running `nurb serve` that has to still answer /health afterwards.
"""

import contextlib
import json
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

from nurb import db, engine_run, folder

SERVE = [sys.executable, "-m", "nurb.serve"]

# The same kernel call issue #247 named, reached directly: an adaptor with no curve
# dereferences null in `D0`. No Python traceback, no exception, just a dead process.
CRASHING = """from nurb import *
from OCP.Geom2dAdaptor import Geom2dAdaptor_Curve
from OCP.gp import gp_Pnt2d


@part
def bracket(width=40.0, draft=False):
    body = Box(width, 20, 5)
    Geom2dAdaptor_Curve().D0(0.0, gp_Pnt2d())
    return body
"""

CUBE = """from nurb import *


@part
def cube():
    return Box(10, 10, 10)
"""

PART = """from nurb import *


@part
def thing(width=40.0, depth=30.0, height=5.0):
    return Box(width, depth, height)
"""

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


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    conn = db.connect(tmp_path / "x.db")
    yield conn
    conn.close()


def run_row(conn, run_id):
    return conn.execute("SELECT * FROM build_runs WHERE id = ?", (run_id,)).fetchone()


def test_a_kernel_fault_is_an_error_and_the_next_build_still_runs(conn):
    """A segfault inside OCCT ends as one error row, not a dead process."""
    project_id = db.create_project(conn, "scratchpad")
    bracket = db.create_part(conn, project_id, "bracket", CRASHING)
    cube = db.create_part(conn, project_id, "cube", CUBE)

    run_id, result = engine_run.run_build(conn, bracket)
    row = run_row(conn, run_id)
    assert row["status"] == "error"
    assert "engine stopped" in row["error"], row["error"]
    assert result["glb_bytes"] is None

    next_run, next_result = engine_run.run_build(conn, cube)
    assert run_row(conn, next_run)["status"] == "ok"
    assert next_result["glb_bytes"]


def test_two_builds_of_the_same_configuration_share_a_glb_hash(conn):
    """The rule an estimate hangs on. A rebuild that changed nothing must not read as
    a new shape, or the answer the user just paid a slicer for deletes itself."""
    project_id = db.create_project(conn, "scratchpad")
    thing = db.create_part(conn, project_id, "thing", PART)

    first = json.loads(run_row(conn, engine_run.run_build(conn, thing)[0])["stats"])["glb_hash"]
    again = json.loads(run_row(conn, engine_run.run_build(conn, thing)[0])["stats"])["glb_hash"]
    assert first == again

    run_id, _ = engine_run.run_build(conn, thing, overrides={"width": 15.0})
    assert json.loads(run_row(conn, run_id)["stats"])["glb_hash"] != first


def test_a_build_landing_on_a_variant_is_judged_by_that_variants_settings(conn):
    """Overrides sitting exactly on a card variant get that variant's settings, and one
    step off puts the base part's rules back."""
    project_id = db.create_project(conn, "scratchpad")
    thing = db.create_part(conn, project_id, "thing", PART, card_md=CARD)

    def rules(overrides):
        return [f["rule"] for f in engine_run.run_build(conn, thing, overrides=overrides)[1]["findings"]]

    assert "min_wall" in rules(None)  # the base card demands 10mm of a 5mm plate
    assert "min_wall" not in rules({"width": 15.0})  # the slim variant allows 1mm
    assert "min_wall" in rules({"width": 14.0})


# --- the same containment, through a running serve ----------------------------


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def state_of(home):
    return json.loads((home / "serve.json").read_text(encoding="utf-8"))


def get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.status, resp.read()


def post_mcp(url, body, token):
    request = urllib.request.Request(
        f"{url}/mcp",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(request, timeout=300) as resp:
        return resp.status, json.loads(resp.read())


@contextlib.contextmanager
def serving(home, port):
    log = home / "test-serve.log"
    with open(log, "w", encoding="utf-8") as sink:
        proc = subprocess.Popen(
            [*SERVE, "--port", str(port)],
            env={**os.environ, "NURB_HOME": str(home)},
            stdout=sink,
            stderr=sink,
        )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            with contextlib.suppress(Exception):
                if get(f"{url}/health", timeout=1)[0] == 200:
                    break
            assert proc.poll() is None, f"serve exited: {log.read_text()}"
            time.sleep(0.1)
        else:
            raise AssertionError(f"serve never answered /health: {log.read_text()}")
        yield url
    finally:
        proc.kill()
        proc.wait()


def test_a_kernel_fault_does_not_take_the_serve_down(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("NURB_HOME", str(home))
    project = tmp_path / "faulty"
    (project / "parts").mkdir(parents=True)
    (project / "parts" / "bracket.py").write_text(CRASHING, encoding="utf-8")

    conn = db.connect()
    project_id, _ = folder.import_folder(conn, project)
    conn.close()

    with serving(home, free_port()) as url:
        status, answer = post_mcp(
            url,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "run_build",
                    "arguments": {"project_id": project_id, "part_name": "bracket"},
                },
            },
            state_of(home)["token"],
        )
        assert status == 200
        assert "engine stopped" in json.dumps(answer["result"])
        assert get(f"{url}/health")[0] == 200

    conn = db.connect(home / "nurb.db")
    try:
        row = conn.execute(
            "SELECT status, error FROM build_runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    assert row["status"] == "error"
    assert "engine stopped" in row["error"]
