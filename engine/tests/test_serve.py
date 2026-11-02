"""The serving process and its routes.

Everything here runs the serve as a subprocess with NURB_HOME pointed at a tmp path, so
a developer's own database and their running serve are never in the picture.
"""

import contextlib
import json
import os
import pathlib
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest

SERVE = [sys.executable, "-m", "nurb.serve"]
NOTCH = pathlib.Path(__file__).parents[1] / "examples" / "notch"
TOOLS_JSON = pathlib.Path(__file__).parents[1] / "src" / "nurb" / "tools.json"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def home(tmp_path, monkeypatch):
    where = tmp_path / "home"
    where.mkdir()
    monkeypatch.setenv("NURB_HOME", str(where))
    yield where
    kill_serve(where)


def tool_names():
    return sorted(tool["name"] for tool in json.loads(TOOLS_JSON.read_text(encoding="utf-8")))


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def state_of(home):
    try:
        return json.loads((home / "serve.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill_serve(home):
    state = state_of(home)
    if state and alive(state["pid"]):
        with contextlib.suppress(OSError):
            os.kill(state["pid"], 9)


def get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.status, resp.headers, resp.read()


def post_mcp(url, body, token=None):
    request = urllib.request.Request(
        f"{url}/mcp",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=60) as resp:
        return resp.status, json.loads(resp.read())


@contextlib.contextmanager
def serving(home, port=None, command=SERVE):
    """A serve on `port`, or on whatever it picks for itself when none is asked for."""
    log = home / "test-serve.log"
    with open(log, "w", encoding="utf-8") as sink:
        proc = subprocess.Popen(
            [*command, *(["--port", str(port)] if port else [])],
            env={**os.environ, "NURB_HOME": str(home)},
            stdout=sink,
            stderr=sink,
        )
    url = f"http://127.0.0.1:{port}" if port else None
    try:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if url is None:
                # A killed predecessor leaves its serve.json behind, so only the file
                # this process published names the port it is listening on.
                state = state_of(home)
                url = state["url"] if state and state["pid"] == proc.pid else None
            if url:
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


def test_a_home_keeps_its_token_and_port_across_serves(home):
    """A connect command the user pasted into an agent has to keep working after a
    restart, so the token and the port outlive the process that minted them."""
    asked = free_port()
    with serving(home, asked):
        first = state_of(home)
    assert first["port"] == asked

    with serving(home) as url:  # nothing asked for: it goes back where it was
        again = state_of(home)
    assert url == f"http://127.0.0.1:{asked}"
    assert (again["token"], again["port"]) == (first["token"], asked)

    moved = free_port()
    with serving(home, moved):
        third = state_of(home)
    assert (third["port"], third["token"]) == (moved, first["token"])
    saved = json.loads((home / "connect.json").read_text(encoding="utf-8"))
    assert saved == {"token": first["token"], "port": moved}
    assert stat.S_IMODE((home / "connect.json").stat().st_mode) == 0o600


def test_checkout_writes_the_project_out_as_a_folder(home, tmp_path):
    """The way a user gets their parts as files, and the refusal that keeps a
    checkout from writing over a folder that already holds something."""
    from nurb import db, folder

    conn = db.connect()
    project_id, _ = folder.import_folder(conn, NOTCH)
    conn.close()

    target = tmp_path / "checked-out"
    with serving(home, free_port()) as url:
        answer = json.loads(post(f"{url}/api/projects/{project_id}/checkout", {"directory": str(target)})[2])
        assert answer["directory"] == str(target)
        assert sorted(answer["parts"]) == sorted(py.stem for py in (target / "parts").glob("*.py"))
        assert answer["parts"] and all((target / "parts" / f"{name}.py").is_file() for name in answer["parts"])

        with pytest.raises(urllib.error.HTTPError) as refused:
            post(f"{url}/api/projects/{project_id}/checkout", {"directory": str(target)})
        assert refused.value.code == 400
        assert "already has files in it" in json.loads(refused.value.read())["error"]

        with pytest.raises(urllib.error.HTTPError) as missing:
            post(f"{url}/api/projects/nosuchproject/checkout", {"directory": str(tmp_path / "nope")})
        assert missing.value.code == 404


def test_second_serve_prints_first_url(home):
    port = free_port()
    with serving(home, port):
        first = state_of(home)
        second = subprocess.run(
            [*SERVE, "--port", str(port)],
            env={**os.environ, "NURB_HOME": str(home)},
            capture_output=True,
            text=True,
            timeout=60,
        )
    assert second.returncode == 0, second.stderr
    assert f"http://127.0.0.1:{port}" in second.stdout
    assert state_of(home)["pid"] == first["pid"]


def test_glb_route_serves_latest_ok_build(home):
    from nurb import db, engine_run, folder

    conn = db.connect()
    project_id, _ = folder.import_folder(conn, NOTCH)
    part = conn.execute(
        "SELECT id FROM parts WHERE project_id = ? AND name = 'shelf_basic'", (project_id,)
    ).fetchone()["id"]
    run_id, _ = engine_run.run_build(conn, part)
    assert conn.execute("SELECT status FROM build_runs WHERE id = ?", (run_id,)).fetchone()[0] == "ok"
    conn.close()

    with serving(home, free_port()) as url:
        status, headers, body = get(f"{url}/glb/{project_id}/shelf_basic.glb")
        assert status == 200
        assert body[:4] == b"glTF"
        assert headers["Content-Type"] == "model/gltf-binary"
        assert headers["Cache-Control"] == "no-store"

        with pytest.raises(urllib.error.HTTPError) as never_built:
            get(f"{url}/glb/{project_id}/shelf_gridfinity.glb")
        assert never_built.value.code == 404



def test_the_workbench_read_side(home):
    """One boot, one build: the list, the detail, the picture and the page."""
    from nurb import db, engine_run, folder

    conn = db.connect()
    project_id, _ = folder.import_folder(conn, NOTCH)
    part = conn.execute(
        "SELECT id FROM parts WHERE project_id = ? AND name = 'shelf_basic'", (project_id,)
    ).fetchone()["id"]
    engine_run.run_build(conn, part)
    conn.close()

    with serving(home, free_port()) as url:
        listed = json.loads(get(f"{url}/api/projects")[2])["projects"]
        assert [p["id"] for p in listed] == [project_id]
        assert listed[0]["parts"] == 13
        assert listed[0]["last_built"] > listed[0]["created_at"]

        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        shelf = next(p for p in detail["parts"] if p["name"] == "shelf_basic")
        assert shelf["revision"] == 1
        assert shelf["build"]["status"] == "ok"
        assert shelf["build"]["stale"] is False
        assert shelf["build"]["passed"] is True
        # The page reads the stored stats, not the transcript card's renamed ones.
        assert {"bbox", "volume", "ms"} <= shelf["build"]["stats"].keys()
        assert shelf["params"]
        assert {p["kind"] for p in shelf["params"]} <= {"float", "int", "bool", "str"}
        assert shelf["build"]["glb_url"].endswith(f"?run={shelf['build']['id']}")
        assert shelf["build"]["render_url"].endswith(f"?run={shelf['build']['id']}")

        with pytest.raises(urllib.error.HTTPError) as unknown:
            get(f"{url}/api/projects/nosuchproject")
        assert unknown.value.code == 404
        assert json.loads(unknown.value.read())["error"] == "no project"

        status, headers, body = get(f"{url}/render/{project_id}/shelf_basic.png")
        assert status == 200
        assert headers["Content-Type"] == "image/png"
        assert body[:8] == b"\x89PNG\r\n\x1a\n"

        with pytest.raises(urllib.error.HTTPError) as never_built:
            get(f"{url}/render/{project_id}/shelf_gridfinity.png")
        assert never_built.value.code == 404


def test_the_root_serves_the_workbench_or_says_how_to_build_it(home):
    from nurb import serve

    with serving(home, free_port()) as url:
        if (serve.WORKBENCH / "index.html").is_file():
            status, headers, body = get(f"{url}/")
            assert status == 200
            assert headers["Content-Type"].startswith("text/html")
            assert headers["Cache-Control"] == "no-store"
            assert b'id="root"' in body
        else:
            with pytest.raises(urllib.error.HTTPError) as unbuilt:
                get(f"{url}/")
            assert unbuilt.value.code == 503
            assert unbuilt.value.read().decode() == (
                "the workbench is not built; run: npm install"
                " && npm run build --workspace packages/workbench"
            )


def test_the_websocket_announces_builds_and_messages(home):
    """A write through a tool reaches a page that never asked for anything."""
    from websockets.sync.client import connect

    from nurb import db, folder

    conn = db.connect()
    project_id, _ = folder.import_folder(conn, NOTCH)
    part = conn.execute(
        "SELECT id, current_revision_id FROM parts WHERE project_id = ? AND name = 'shelf_basic'",
        (project_id,),
    ).fetchone()
    source = conn.execute(
        "SELECT source FROM part_revisions WHERE id = ?", (part["current_revision_id"],)
    ).fetchone()["source"]
    conn.close()
    edited = source.replace("lip_height=5.0", "lip_height=5.5", 1)
    assert edited != source

    with serving(home, free_port()) as url:
        with connect(url.replace("http://", "ws://") + "/ws", open_timeout=10) as socket:
            status, answer = post_mcp(
                url,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "write_part_source",
                        "arguments": {
                            "project_id": project_id,
                            "part_name": "shelf_basic",
                            "source": edited,
                            "note": "thicker wall",
                        },
                    },
                },
                token=state_of(home)["token"],
            )
            assert status == 200 and answer["result"].get("isError") is not True

            kinds = set()
            deadline = time.monotonic() + 10
            while {"build", "message"} - kinds and time.monotonic() < deadline:
                event = json.loads(socket.recv(timeout=deadline - time.monotonic()))
                assert event["project_id"] == project_id
                kinds.add(event["kind"])
            assert {"build", "message"} <= kinds

        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        last = detail["messages"][-1]
        assert last["content"] == "thicker wall"
        assert last["payload"]["type"] == "build"
        assert [step["verb"] for step in last["payload"]["build"]["steps"]] == ["build"]
        assert last["payload"]["build"]["part_name"] == "shelf_basic"


def test_mcp_bearer_required(home):
    with serving(home, free_port()) as url:
        call = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        with pytest.raises(urllib.error.HTTPError) as refused:
            post_mcp(url, call)
        assert refused.value.code == 401

        status, payload = post_mcp(url, call, token=state_of(home)["token"])
        assert status == 200
        assert sorted(tool["name"] for tool in payload["result"]["tools"]) == tool_names()


def test_serve_rejects_non_loopback_hosts_on_every_route(home):
    port = free_port()
    with serving(home, port) as url:
        call = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode()
        requests = [
            urllib.request.Request(f"{url}/health", headers={"Host": "attacker.example"}),
            urllib.request.Request(f"{url}/", headers={"Host": "attacker.example"}),
            urllib.request.Request(f"{url}/api/projects", headers={"Host": "attacker.example"}),
            urllib.request.Request(
                f"{url}/glb/project/part.glb", headers={"Host": "attacker.example"}
            ),
            urllib.request.Request(
                f"{url}/render/project/part.png", headers={"Host": "attacker.example"}
            ),
            urllib.request.Request(
                f"{url}/mcp",
                data=call,
                headers={
                    "Host": "attacker.example",
                    "Authorization": f"Bearer {state_of(home)['token']}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            ),
        ]
        for request in requests:
            with pytest.raises(urllib.error.HTTPError) as refused:
                urllib.request.urlopen(request, timeout=10)
            assert refused.value.code == 400
            assert refused.value.read() == b"Invalid host header"

        for host in (f"127.0.0.1:{port}", f"localhost:{port}"):
            request = urllib.request.Request(f"{url}/health", headers={"Host": host})
            with urllib.request.urlopen(request, timeout=10) as response:
                assert response.status == 200
                assert json.load(response)["ok"] is True


def test_a_non_ascii_token_is_refused_not_crashed(home):
    with serving(home, free_port()) as url:
        request = urllib.request.Request(
            f"{url}/mcp",
            data=b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}',
            headers={"Content-Type": "application/json"},
        )
        request.add_header("Authorization", "Bearer töken")
        with pytest.raises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(request, timeout=10)
        assert refused.value.code == 401


def test_sigterm_removes_the_state_file(home):
    """uvicorn re-raises the signal after its shutdown, which would skip the cleanup
    that keeps a client from waiting on a port nobody listens to."""
    import signal

    with serving(home, free_port()) as url:
        pid = state_of(home)["pid"]
        os.kill(pid, signal.SIGTERM)
        # The serve is this test's child, so kill(0) would still answer for its
        # zombie; the port going quiet is the honest sign it is gone.
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                get(f"{url}/health", timeout=1)
            except Exception:
                break
            time.sleep(0.1)
        else:
            raise AssertionError("serve still answers after SIGTERM")
        # The listener closes before the cleanup that removes the file runs.
        while state_of(home) is not None and time.monotonic() < deadline:
            time.sleep(0.1)
        assert state_of(home) is None


def test_published_url_ignores_a_dead_predecessor(monkeypatch):
    from nurb import serve

    stale = {"url": "http://127.0.0.1:7001", "pid": 1}
    fresh = {"url": "http://127.0.0.1:7002", "pid": 2}
    states = iter((stale, stale, fresh))
    monkeypatch.setattr(serve, "read_state", lambda: next(states))
    monkeypatch.setattr(serve, "_state_alive", lambda state: state["pid"] == 2)
    monkeypatch.setattr(serve.time, "sleep", lambda seconds: None)

    assert serve._published_url() == fresh["url"]


def test_messages_map_to_the_four_card_shapes(home):
    """The transcript's payloads, shaped without a serve in the picture."""
    from nurb import db, serve

    conn = db.connect()
    project_id = db.create_project(conn, "mapping")
    part_id = db.create_part(conn, project_id, "cube", "from nurb import *\n")
    revision_id = conn.execute(
        "SELECT current_revision_id FROM parts WHERE id = ?", (part_id,)
    ).fetchone()[0]
    run_id = db.new_id()
    with db.transaction(conn):
        conn.execute(
            "INSERT INTO build_runs (id, revision_id, status, findings, stats, started_at, finished_at)"
            " VALUES (?, ?, 'ok', ?, ?, '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:02+00:00')",
            (
                run_id,
                revision_id,
                json.dumps([{"rule": "sliver", "severity": "warn", "message": "thin", "face": [1.0]}]),
                json.dumps({"bbox": [1.0, 2.0, 3.0], "volume": 6.0, "ms": 1500}),
            ),
        )
    db.set_measurement(conn, project_id, "shelf_gap", 12.5, "calipers")

    db.add_message(conn, project_id, "assistant", "thicker", {"tool": "run_build", "summary": "cube built", "run_id": run_id, "part_name": "cube"})
    db.add_message(conn, project_id, "assistant", None, {"tool": "pin_spec", "summary": "pinned", "type": "spec_pinned", "spec": {"part_name": "cube"}, "input": {}})
    db.add_message(conn, project_id, "assistant", None, {"tool": "record_measurement", "summary": "recorded shelf_gap = 12.5 mm", "measurement": "shelf_gap", "previous_value_mm": 12.0, "stale_parts": ["cube"]})
    db.add_message(conn, project_id, "assistant", None, {"tool": "create_project", "summary": "created project mapping"})

    rows = conn.execute(
        "SELECT * FROM messages WHERE project_id = ? ORDER BY sequence_number", (project_id,)
    ).fetchall()
    shaped = [serve._message(conn, row) for row in rows]
    conn.close()

    assert [m["payload"]["type"] for m in shaped] == ["build", "spec", "measurement", "step"]

    build = shaped[0]["payload"]["build"]
    assert build["status"] == "passed"
    assert build["revision"] == 1
    assert build["elapsed_s"] == 2.0
    assert build["stats"] == {"size_mm": [1.0, 2.0, 3.0], "volume_mm3": 6.0, "build_s": 1.5}
    assert "face" not in build["findings"][0]
    assert build["glb_url"] == f"/glb/{project_id}/cube.glb?run={run_id}"
    assert build["steps"][0] == {
        "id": run_id,
        "verb": "build",
        "object": "cube",
        "status": "done",
        "started_at": "2026-01-01T00:00:00+00:00",
        "elapsed_s": 2.0,
        "output": "cube built",
    }

    assert shaped[1]["payload"]["spec"] == {"part_name": "cube"}
    assert shaped[2]["payload"]["measurement"] == {
        "name": "shelf_gap",
        "value_mm": 12.5,
        "how": "calipers",
        "provisional": False,
        "previous_value_mm": 12.0,
        "stale_parts": ["cube"],
    }
    assert shaped[3]["payload"]["step"]["verb"] == "create"
    assert shaped[3]["payload"]["step"]["object"] == "mapping"


def test_a_failed_build_keeps_the_last_good_picture(home):
    """The geometry on screen outlives a broken edit, and says it is stale."""
    from nurb import db, serve

    conn = db.connect()
    project_id = db.create_project(conn, "fallback")
    part_id = db.create_part(conn, project_id, "cube", "from nurb import *\n")
    good_revision = conn.execute(
        "SELECT current_revision_id FROM parts WHERE id = ?", (part_id,)
    ).fetchone()[0]
    ok_run = db.new_id()
    with db.transaction(conn):
        conn.execute(
            "INSERT INTO build_runs (id, revision_id, status, findings, stats, glb, started_at, finished_at)"
            " VALUES (?, ?, 'ok', '[]', '{}', ?, '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:01+00:00')",
            (ok_run, good_revision, b"glTF fake"),
        )
    broken_revision = db.add_revision(conn, part_id, "from nurb import *\nraise ValueError('boom')\n")
    with db.transaction(conn):
        conn.execute(
            "INSERT INTO build_runs (id, revision_id, status, error, findings, stats, started_at, finished_at)"
            " VALUES (?, ?, 'error', 'ValueError: boom', ?, '{}', '2026-01-01T00:00:02+00:00', '2026-01-01T00:00:03+00:00')",
            (
                db.new_id(),
                broken_revision,
                json.dumps([{"rule": "wall", "severity": "fail", "message": "thin", "face": [1.0]}]),
            ),
        )

    detail = serve._project(conn, project_id)
    conn.close()

    build = next(p for p in detail["parts"] if p["name"] == "cube")["build"]
    assert build["status"] == "error"
    assert build["passed"] is False
    assert build["error"] == "ValueError: boom"
    # The viewer glows the guilty triangles, so the detail keeps the face the
    # transcript's build card drops.
    assert build["findings"][0]["face"] == [1.0]
    assert build["glb_url"] == f"/glb/{project_id}/cube.glb?run={ok_run}"
    assert build["stale"] is True


SLAB = """from nurb import *


@part
def slab(width=100.0, height=20.0, count=2):
    return Box(width, height, 5.0 * count)
"""


def post(url, payload, timeout=300):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return resp.status, resp.headers, resp.read()


def patch(url, payload, timeout=60):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return resp.status, resp.headers, resp.read()


def delete(url, timeout=60):
    request = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return resp.status, resp.headers, resp.read()


def a_slab():
    """A one-part project with one build: what every write route needs in place."""
    from nurb import db, engine_run

    conn = db.connect()
    project_id = db.create_project(conn, "slabs")
    part_id = db.create_part(conn, project_id, "slab", SLAB)
    run_id, _ = engine_run.run_build(conn, part_id)
    assert conn.execute("SELECT status FROM build_runs WHERE id = ?", (run_id,)).fetchone()[0] == "ok"
    conn.close()
    return project_id, part_id


def test_a_part_that_never_built_builds_from_the_stage(home):
    """The first build has no values to type, so an empty map is not a refusal."""
    from nurb import db

    conn = db.connect()
    project_id = db.create_project(conn, "slabs")
    part_id = db.create_part(conn, project_id, "slab", SLAB)
    conn.close()

    with serving(home, free_port()) as url:
        before = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        first = next(p for p in before["parts"] if p["name"] == "slab")
        assert first["build"] is None
        assert first["params"] == []

        answer = json.loads(post(f"{url}/api/parts/{part_id}/params", {"values": {}})[2])
        assert answer["build"]["status"] == "ok"

        after = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        built = next(p for p in after["parts"] if p["name"] == "slab")
        assert built["build"]["status"] == "ok"
        assert [p["name"] for p in built["params"]] == ["width", "height", "count"]


def test_the_sliders_build_and_then_land_in_the_signature(home):
    from nurb import db

    project_id, part_id = a_slab()
    with serving(home, free_port()) as url:
        before = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        first = next(p for p in before["parts"] if p["name"] == "slab")
        assert first["overrides"] == {}
        assert before["printer"] is None
        assert before["printers"] == []  # nothing in the workshop yet

        # Exploring: a build at these values, with the source untouched.
        answer = json.loads(
            post(f"{url}/api/parts/{part_id}/params", {"values": {"width": 116, "count": 3}})[2]
        )
        assert answer["build"]["status"] == "ok"
        assert answer["build"]["id"] != first["build"]["id"]
        assert answer["build"]["slice"] is None

        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        part = next(p for p in detail["parts"] if p["name"] == "slab")
        assert part["overrides"] == {"width": 116.0, "count": 3}
        assert part["revision"] == 1  # exploring writes no revision

        # Applying: the same values, now in the signature, as a new revision.
        applied = json.loads(
            post(f"{url}/api/parts/{part_id}/apply", {"values": {"width": 116, "count": 3}})[2]
        )
        assert applied["written"] == ["count", "width"]
        assert applied["skipped"] == []
        assert applied["revision"] == 2
        assert applied["build"]["status"] == "ok"

        conn = db.connect()
        try:
            revision = conn.execute(
                "SELECT * FROM part_revisions WHERE id = ?", (applied["revision_id"],)
            ).fetchone()
            assert revision["parent_id"] == first["revision_id"]
            assert "width=116.0" in revision["source"]
            assert "count=3" in revision["source"]
            assert revision["note"] == "Applied count, width from the sliders"
            run = conn.execute(
                "SELECT * FROM build_runs WHERE id = ?", (applied["build"]["id"],)
            ).fetchone()
            assert json.loads(run["overrides"]) == {}
            assert run["revision_id"] == applied["revision_id"]
        finally:
            conn.close()

        # The transcript shows the apply as a build, like any a tool ran.
        after = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        last = after["messages"][-1]
        assert last["payload"]["type"] == "build"
        assert last["payload"]["build"]["id"] == applied["build"]["id"]
        assert next(p for p in after["parts"] if p["name"] == "slab")["source"].count("width=116.0") == 1

        # Applying nothing new writes no revision.
        again = json.loads(post(f"{url}/api/parts/{part_id}/apply", {"values": {"width": 116}})[2])
        assert again["written"] == []
        assert again["revision"] == 2


def test_the_write_routes_refuse_what_they_cannot_do(home):
    project_id, part_id = a_slab()
    with serving(home, free_port()) as url:
        for route in ("params", "apply", "export"):
            request = urllib.request.Request(
                f"{url}/api/parts/{part_id}/{route}",
                data=b"{not json",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as bad:
                urllib.request.urlopen(request, timeout=30)
            assert bad.value.code == 400
            assert json.loads(bad.value.read())["error"] == "the request body must be JSON"

        with pytest.raises(urllib.error.HTTPError) as unknown:
            post(f"{url}/api/parts/nosuchpart/params", {"values": {}})
        assert unknown.value.code == 404
        assert json.loads(unknown.value.read())["error"] == "no such part"

        with pytest.raises(urllib.error.HTTPError) as nonsense:
            post(f"{url}/api/parts/{part_id}/params", {"values": {"nope": 1}})
        assert nonsense.value.code == 400
        assert "no parameter named nope" in json.loads(nonsense.value.read())["error"]

        with pytest.raises(urllib.error.HTTPError) as unformatted:
            post(f"{url}/api/parts/{part_id}/export", {"format": "obj"})
        assert unformatted.value.code == 400

        with pytest.raises(urllib.error.HTTPError) as unmade:
            post(f"{url}/api/projects/{project_id}/printer", {"profile": "nosuchprinter"})
        assert unmade.value.code == 400
        assert "no printer profile called" in json.loads(unmade.value.read())["error"]


def test_the_download_the_load_case_and_the_print_estimate(home):
    from nurb import db

    project_id, part_id = a_slab()
    with serving(home, free_port()) as url:
        expected = {
            "3mf": (b"PK", "model/3mf"),
            "stl": (None, "model/stl"),
            "step": (b"ISO-10303-21;", "application/step"),
            "glb": (b"glTF", "model/gltf-binary"),
        }
        for fmt, (magic, mime) in expected.items():
            status, headers, body = post(f"{url}/api/parts/{part_id}/export", {"format": fmt})
            assert status == 200
            assert headers["Content-Type"] == mime
            assert headers["Content-Disposition"] == f'attachment; filename="slab.{fmt}"'
            if magic:
                assert body[: len(magic)] == magic
            if fmt == "3mf":
                assert headers["X-Nurb-Print-Settings"]
            if fmt == "glb":
                conn = db.connect()
                try:
                    stored = db.latest_ok_run(conn, part_id)["glb"]
                finally:
                    conn.close()
                assert body == stored

        # No printer named yet, so the answer is a picker rather than a sentence.
        # Without a slicer installed there is no answer to give at all.
        estimate = json.loads(post(f"{url}/api/parts/{part_id}/slice", {}, timeout=600)[2])
        assert estimate["kind"] in ("choose", "slicer")
        if estimate["kind"] == "choose":
            assert estimate["profiles"] == []

        named = json.loads(
            post(f"{url}/api/projects/{project_id}/printer", {"profile": "bambu_x1c"})[2]
        )
        assert named["printer"]["name"] == "bambu_x1c"
        assert len(named["printer"]["bed"]) == 3
        conn = db.connect()
        try:
            assert 'profile = "bambu_x1c"' in db.get_project(conn, project_id)["printer_toml"]
        finally:
            conn.close()
        assert json.loads(get(f"{url}/api/projects/{project_id}")[2])["printer"] == named["printer"]

        estimate = json.loads(post(f"{url}/api/parts/{part_id}/slice", {}, timeout=600)[2])
        assert estimate["kind"] in ("slice", "slicer", "profile", "build")
        if estimate["kind"] == "slice":
            assert estimate["profile"] == "bambu_x1c"
            assert estimate["spoken"] and estimate["weight"]
            conn = db.connect()
            try:
                assert conn.execute(
                    "SELECT slice FROM build_runs WHERE id = ?", (estimate["run_id"],)
                ).fetchone()[0]
            finally:
                conn.close()


SWITCHED = """from nurb import *


@part
def switched(width=100.0, count=2, wall_thickness=2.0, solid=True, label="plate"):
    return Box(width, 20.0 + wall_thickness, 5.0 * count)
"""


def a_switched():
    """A part with one of every kind of parameter, built once."""
    from nurb import db, engine_run

    conn = db.connect()
    project_id = db.create_project(conn, "switches")
    part_id = db.create_part(conn, project_id, "switched", SWITCHED)
    engine_run.run_build(conn, part_id)
    conn.close()
    return project_id, part_id


def refused(url, payload):
    with pytest.raises(urllib.error.HTTPError) as bad:
        post(url, payload)
    return bad.value.code, json.loads(bad.value.read())["error"]


def test_a_value_that_is_not_the_kind_it_names_is_refused(home):
    """Typing is the whole guard here: JSON carries NaN, Infinity and "false", and
    every one of them builds something wrong or nothing at all."""
    project_id, part_id = a_switched()
    with serving(home, free_port()) as url:
        params = f"{url}/api/parts/{part_id}/params"
        # NaN reaches OCCT as a dimension it grinds on until the build deadline, and
        # is then stored as an override that no JSON reader will take back.
        assert refused(params, {"values": {"width": float("nan")}})[1] == (
            "width takes a number, not nan"
        )
        assert refused(params, {"values": {"width": float("inf")}})[0] == 400
        assert refused(params, {"values": {"count": float("inf")}})[0] == 400
        # An integer too large to be a float overflows the finite check rather than
        # failing it, and answered 500 until it was caught.
        assert refused(params, {"values": {"count": 10**400}})[0] == 400
        assert refused(params, {"values": {"solid": "false"}})[1] == (
            "solid is on or off, not 'false'"
        )
        assert refused(params, {"values": {"label": "wide"}})[1] == (
            "label is not a number, so the sliders cannot set it"
        )

        # A switch the page did send as a switch still lands.
        answer = json.loads(post(params, {"values": {"solid": False, "count": 3}})[2])
        assert answer["build"]["status"] == "ok"

        # Nothing refused was stored, so the page still reads.
        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        assert next(p for p in detail["parts"] if p["name"] == "switched")["overrides"] == {
            "solid": False,
            "count": 3,
        }


def test_a_failed_build_keeps_the_sliders(home):
    """The parameters come off the newest build that reported any. A build that raised
    before the signature was read reports none, and losing them would mean a part that
    cannot be explored back out of its own bad edit."""
    from nurb import db

    project_id, part_id = a_slab()
    conn = db.connect()
    db.add_revision(conn, part_id, SLAB.replace("return Box", "raise ValueError('boom')\n    return Box"))
    conn.close()

    with serving(home, free_port()) as url:
        broken = json.loads(post(f"{url}/api/parts/{part_id}/params", {"values": {}})[2])
        assert broken["build"]["status"] == "error"

        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        part = next(p for p in detail["parts"] if p["name"] == "slab")
        assert [p["name"] for p in part["params"]] == ["width", "height", "count"]

        again = json.loads(post(f"{url}/api/parts/{part_id}/params", {"values": {"width": 90}})[2])
        assert again["build"]["status"] == "error"


def test_a_slice_of_a_part_that_is_not_there_is_a_sentence(home):
    """Every route answers a missing part the same way, and none of them answer 500."""
    a_slab()
    with serving(home, free_port()) as url:
        with pytest.raises(urllib.error.HTTPError) as missing:
            post(f"{url}/api/parts/nosuchpart/slice", {})
        assert missing.value.code == 404
        assert json.loads(missing.value.read())["error"] == "no such part"


# A serve whose slicer takes five seconds and is found without one being installed.
SLOW_SLICER = [
    sys.executable,
    "-c",
    """
import pathlib, runpy, sys, time
from nurb import slicing
def run(model, target, *args, **kwargs):
    time.sleep(5)
    return (3600, 12.0), pathlib.Path(target)
slicing.app = lambda search=None: pathlib.Path("/slow/OrcaSlicer")
slicing.vendors = lambda exe: pathlib.Path("/slow")
slicing.machine = lambda bundle, name: pathlib.Path("/slow/machine.json")
slicing.profiles_for = lambda *a: (pathlib.Path("/slow/process.json"), pathlib.Path("/slow/pla.json"))
slicing.run = run
sys.argv = ["nurb.serve", *sys.argv[1:]]
runpy.run_module("nurb.serve", run_name="__main__")
""",
]


def test_a_slice_in_flight_leaves_the_server_free(home):
    """Every build starts a slice, and a slicer can take minutes. A slider drag or a
    chat write that waits behind it looks like a frozen app (issue #296)."""
    import threading

    project_id, part_id = a_slab()
    with serving(home, free_port(), command=SLOW_SLICER) as url:
        post(f"{url}/api/projects/{project_id}/printer", {"profile": "bambu_x1c"})
        sliced = {}
        slicing = threading.Thread(
            target=lambda: sliced.update(json.loads(post(f"{url}/api/parts/{part_id}/slice", {})[2]))
        )
        slicing.start()
        time.sleep(1.5)  # the slice is under way
        started = time.monotonic()
        get(f"{url}/api/projects/{project_id}")
        assert time.monotonic() - started < 2
        slicing.join()
        assert sliced["kind"] == "slice" and sliced["seconds"] == 3600


def test_a_refusal_about_a_broken_part_is_one_sentence(home):
    """A run's error is the user's traceback. The build card has room for it; a
    download that cannot happen gets the last line of it."""
    from nurb import db

    _, part_id = a_slab()
    conn = db.connect()
    db.add_revision(conn, part_id, SLAB.replace("return Box", "raise ValueError('boom')\n    return Box"))
    conn.close()

    with serving(home, free_port()) as url:
        for route, payload in (
            ("export", {"format": "glb"}),
            ("export", {"format": "stl"}),
        ):
            code, said = refused(f"{url}/api/parts/{part_id}/{route}", payload)
            assert code == 409
            # One line, the user's own words, and no path out of the scratch folder.
            assert "\n" not in said and said.endswith("boom"), (route, payload, said)


def test_the_transcript_names_a_parameter_the_way_the_slider_does(home):
    """The person reading it owns a printer; wall_thickness is a name from a signature."""
    from nurb import db

    project_id, part_id = a_switched()
    with serving(home, free_port()) as url:
        applied = json.loads(
            post(f"{url}/api/parts/{part_id}/apply", {"values": {"wall_thickness": 3.0}})[2]
        )
        assert applied["written"] == ["wall_thickness"]  # the page matches these to sliders

        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        assert detail["messages"][-1]["content"] == (
            "Applied wall thickness from the sliders to switched."
        )
        conn = db.connect()
        try:
            note = conn.execute(
                "SELECT note FROM part_revisions WHERE id = ?", (applied["revision_id"],)
            ).fetchone()["note"]
        finally:
            conn.close()
        assert note == "Applied wall thickness from the sliders"


def preflight(url, origin):
    request = urllib.request.Request(
        url,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
        method="OPTIONS",
    )
    with urllib.request.urlopen(request, timeout=30) as resp:
        return resp.status, resp.headers


def test_only_the_desktop_webview_may_read_the_serve(home):
    with serving(home, free_port()) as url:
        status, headers = preflight(f"{url}/api/projects", "tauri://localhost")
        assert status == 200
        assert headers["access-control-allow-origin"] == "tauri://localhost"

        # The download button reads both of these off an export response.
        request = urllib.request.Request(
            f"{url}/api/projects", headers={"Origin": "http://localhost:1420"}
        )
        with urllib.request.urlopen(request, timeout=30) as resp:
            assert resp.headers["access-control-allow-origin"] == "http://localhost:1420"
            exposed = resp.headers["access-control-expose-headers"]
        assert "Content-Disposition" in exposed and "X-Nurb-Print-Settings" in exposed

        request = urllib.request.Request(
            f"{url}/api/projects", headers={"Origin": "https://example.com"}
        )
        with urllib.request.urlopen(request, timeout=30) as resp:
            assert resp.status == 200
            assert resp.headers.get("access-control-allow-origin") is None


def simple_post(url, origin=None):
    """A POST the way a page on the web can send one: no preflight, so no CORS."""
    request = urllib.request.Request(
        url, data=b"{}", headers={"Content-Type": "text/plain"}, method="POST"
    )
    if origin:
        request.add_header("Origin", origin)
    with urllib.request.urlopen(request, timeout=30) as resp:
        return resp.status


def test_a_page_on_the_web_may_not_write_however_it_sends_it(home):
    with serving(home, free_port()) as url:
        with pytest.raises(urllib.error.HTTPError) as refused:
            simple_post(f"{url}/api/projects", "https://evil.example")
        assert refused.value.code == 403
        assert refused.value.read() == b"this page may not change the workbench"
        assert json.loads(get(f"{url}/api/projects")[2])["projects"] == []

        assert simple_post(f"{url}/api/projects", "tauri://localhost") == 200
        assert simple_post(f"{url}/api/projects") == 200
        assert len(json.loads(get(f"{url}/api/projects")[2])["projects"]) == 2

        # Reads were never the concern; CORS already withholds those answers.
        request = urllib.request.Request(
            f"{url}/api/projects", headers={"Origin": "https://evil.example"}
        )
        with urllib.request.urlopen(request, timeout=30) as resp:
            assert resp.status == 200


def open_socket(url, origin=None):
    """The handshake alone: what a page on the web can try against /ws."""
    from websockets.sync.client import connect

    headers = {"Origin": origin} if origin else {}
    with connect(
        url.replace("http://", "ws://") + "/ws", additional_headers=headers, open_timeout=10
    ) as socket:
        return socket.response.status_code


def test_a_page_on_the_web_may_not_listen_either(home):
    """CORS gates no socket, so a foreign page could otherwise watch every build."""
    from websockets.exceptions import InvalidStatus

    with serving(home, free_port()) as url:
        for origin in ("https://evil.example", "null"):
            with pytest.raises(InvalidStatus) as refused:
                open_socket(url, origin)
            assert refused.value.response.status_code == 403

        assert open_socket(url, "tauri://localhost") == 101
        assert open_socket(url) == 101


def test_a_project_is_made_named_or_not(home):
    with serving(home, free_port()) as url:
        named = json.loads(post(f"{url}/api/projects", {"name": "Shelf"})[2])
        assert named["name"] == "Shelf"

        # A name that is not a name would otherwise land in the list as str(dict).
        with pytest.raises(urllib.error.HTTPError) as refused:
            post(f"{url}/api/projects", {"name": {"a": 1}})
        assert refused.value.code == 400
        assert json.loads(refused.value.read())["error"] == "name must be what to call the project"

        unnamed = json.loads(post(f"{url}/api/projects", {})[2])
        assert unnamed["name"] and unnamed["name"] != "Shelf"
        assert unnamed["id"] != named["id"]

        listed = json.loads(get(f"{url}/api/projects")[2])["projects"]
        assert {p["id"] for p in listed} == {named["id"], unnamed["id"]}


def test_a_folder_is_imported_and_a_folder_without_parts_is_refused(home, tmp_path):
    with serving(home, free_port()) as url:
        imported = json.loads(post(f"{url}/api/import", {"path": str(NOTCH)})[2])
        assert imported["name"] == "notch"
        assert imported["parts"] == 13

        listed = json.loads(get(f"{url}/api/projects")[2])["projects"]
        assert [(p["id"], p["parts"]) for p in listed] == [(imported["id"], 13)]

        empty = tmp_path / "nothing"
        empty.mkdir()
        with pytest.raises(urllib.error.HTTPError) as refused:
            post(f"{url}/api/import", {"path": str(empty)})
        assert refused.value.code == 400
        assert json.loads(refused.value.read())["error"] == f"no parts/ in {empty}"

        gone_path = tmp_path / "missing"
        with pytest.raises(urllib.error.HTTPError) as gone:
            post(f"{url}/api/import", {"path": str(gone_path)})
        assert gone.value.code == 400
        assert json.loads(gone.value.read())["error"] == f"no folder at {gone_path}"

        # A typed path carries a tilde, and the answer names the folder it expands to.
        with pytest.raises(urllib.error.HTTPError) as tilde:
            post(f"{url}/api/import", {"path": "~/no-such-nurb-folder"})
        assert tilde.value.code == 400
        assert json.loads(tilde.value.read())["error"] == (
            f"no folder at {pathlib.Path.home() / 'no-such-nurb-folder'}"
        )


def test_renaming_a_project_keeps_its_parts_where_they_are(home):
    """The name is a label, so a rename moves nothing: the parts and the folder stay."""
    with serving(home, free_port()) as url:
        imported = json.loads(post(f"{url}/api/import", {"path": str(NOTCH)})[2])

        renamed = json.loads(patch(f"{url}/api/projects/{imported['id']}", {"name": "  Notch shelf  "})[2])
        assert renamed["name"] == "Notch shelf"
        assert renamed["parts"] == imported["parts"]

        listed = json.loads(get(f"{url}/api/projects")[2])["projects"]
        assert [(p["id"], p["name"]) for p in listed] == [(imported["id"], "Notch shelf")]
        assert NOTCH.is_dir() and (NOTCH / "parts").is_dir()

        with pytest.raises(urllib.error.HTTPError) as blank:
            patch(f"{url}/api/projects/{imported['id']}", {"name": "   "})
        assert blank.value.code == 400
        assert json.loads(blank.value.read())["error"] == "name must be what to call the project"

        with pytest.raises(urllib.error.HTTPError) as gone:
            patch(f"{url}/api/projects/nosuchproject", {"name": "Shelf"})
        assert gone.value.code == 404
        assert json.loads(gone.value.read())["error"] == "no project"


def test_deleting_a_project_takes_its_parts_with_it(home):
    from nurb import db

    project_id, part_id = a_slab()
    with serving(home, free_port()) as url:
        request = urllib.request.Request(f"{url}/api/projects/{project_id}", method="DELETE")
        with urllib.request.urlopen(request, timeout=30) as resp:
            assert resp.status == 200

        assert json.loads(get(f"{url}/api/projects")[2])["projects"] == []
        with pytest.raises(urllib.error.HTTPError) as again:
            urllib.request.urlopen(
                urllib.request.Request(f"{url}/api/projects/{project_id}", method="DELETE"),
                timeout=30,
            )
        assert again.value.code == 404
        assert json.loads(again.value.read())["error"] == "no project"

    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) FROM parts WHERE id = ?", (part_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM build_runs").fetchone()[0] == 0
    finally:
        conn.close()


def test_the_chat_column_can_write_both_sides_of_a_turn(home):
    """A driver stores what the user asked and what it answered, in order."""
    from nurb import db

    conn = db.connect()
    project_id = db.create_project(conn, "turns")
    conn.close()

    with serving(home, free_port()) as url:
        route = f"{url}/api/projects/{project_id}/messages"
        status, _, body = post(route, {"role": "user", "content": "make it taller"})
        assert status == 201
        said = json.loads(body)
        assert said["role"] == "user"
        assert said["content"] == "make it taller"

        assert post(route, {"role": "assistant", "content": "raised the shelf"})[0] == 201

        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        assert [(m["role"], m["content"]) for m in detail["messages"]] == [
            ("user", "make it taller"),
            ("assistant", "raised the shelf"),
        ]
        # A plain turn draws no card: the column keys the bubble off the role.
        assert [m["payload"] for m in detail["messages"]] == [None, None]

        with pytest.raises(urllib.error.HTTPError) as bad_role:
            post(route, {"role": "system", "content": "hello"})
        assert bad_role.value.code == 400

        with pytest.raises(urllib.error.HTTPError) as empty:
            post(route, {"role": "user", "content": "  "})
        assert empty.value.code == 400

        with pytest.raises(urllib.error.HTTPError) as unknown:
            post(f"{url}/api/projects/nope/messages", {"role": "user", "content": "hi"})
        assert unknown.value.code == 404


def test_a_new_part_claims_the_turns_that_described_it(home):
    from nurb import db

    conn = db.connect()
    shelves = db.create_project(conn, "shelves", folder=True)
    conn.close()
    with serving(home, free_port()) as url:
        route = f"{url}/api/projects/{shelves}/messages"
        before = json.loads(post(route, {"role": "user", "content": "about the whole set"})[2])
        post(route, {"role": "user", "content": "a bin, 40 wide"})
        post(route, {"role": "assistant", "content": "made the bin"})
        conn = db.connect()
        db.create_part(conn, shelves, "bin", SLAB.replace("slab", "bin"))
        conn.close()

        claim = f"{route}/claim"
        assert json.loads(post(claim, {"part": "bin", "after": before["sequence_number"]})[2]) == {"claimed": 2}
        whole = json.loads(get(f"{url}/api/projects/{shelves}")[2])["messages"]
        # The turn from before the new part was started stays the folder's.
        assert [(m["content"], m["part"]) for m in whole] == [
            ("about the whole set", None),
            ("a bin, 40 wide", "bin"),
            ("made the bin", "bin"),
        ]

        with pytest.raises(urllib.error.HTTPError) as unknown:
            post(claim, {"part": "nope", "after": 0})
        assert unknown.value.code == 400
        with pytest.raises(urllib.error.HTTPError) as bad:
            post(claim, {"part": "bin", "after": "x"})
        assert bad.value.code == 400


def test_a_photo_from_the_chat_is_what_find_photos_sees(home):
    import base64
    import io

    from PIL import Image

    from nurb import db, mcp_server

    conn = db.connect()
    project_id = db.create_project(conn, "turns")
    conn.close()

    def jpeg(color):
        buf = io.BytesIO()
        Image.new("RGB", (64, 64), color).save(buf, "JPEG")
        return base64.b64encode(buf.getvalue()).decode()

    with serving(home, free_port()) as url:
        route = f"{url}/api/projects/{project_id}/attachments"
        for name in ("first.jpg", "second.jpg", "third.jpg", "fourth.jpg"):
            sent = {"name": name, "mime": "image/jpeg", "data": jpeg("red")}
            assert post(route, sent)[0] == 201

        for bad in (
            {"name": "../escape.jpg", "mime": "image/jpeg", "data": jpeg("red")},
            {"name": "notes.txt", "mime": "text/plain", "data": jpeg("red")},
            {"name": "x.jpg", "mime": "image/jpeg", "data": "not base64!"},
        ):
            with pytest.raises(urllib.error.HTTPError) as refused:
                post(route, bad)
            assert refused.value.code == 400

    conn = db.connect()
    result = mcp_server.dispatch(conn, "find_photos", {"project_id": project_id, "query": "bracket"}, "http://x")
    conn.close()
    # The newest come back when no name matches: that is what was just attached.
    assert [photo["name"] for photo in json.loads(result.content[0].text)["photos"]] == [
        "fourth.jpg",
        "third.jpg",
        "second.jpg",
    ]


def test_an_attached_mesh_comes_back_as_a_picture_and_its_size(home, tmp_path):
    """The app's way to show an agent a 3MF or STL, since Claude cannot open one."""
    import base64

    from build123d import Box, Mesher

    target = tmp_path / "bracket.3mf"
    mesher = Mesher()
    mesher.add_shape(Box(20, 30, 40))
    mesher.write(str(target))

    with serving(home, free_port()) as url:
        status, _, body = post(f"{url}/api/mesh", {"path": str(target)})
        assert status == 200
        seen = json.loads(body)
        assert '"bracket.3mf": 20 x 30 x 40 mm' in seen["text"]
        assert base64.b64decode(seen["png"]).startswith(b"\x89PNG")

        broken = tmp_path / "broken.3mf"
        broken.write_text("not a zip")
        for sent in ({"path": str(broken)}, {"path": str(tmp_path / "gone.stl")}, {}):
            with pytest.raises(urllib.error.HTTPError) as refused:
                post(f"{url}/api/mesh", sent)
            assert refused.value.code == 400


def test_a_turn_remembers_the_files_sent_with_it(home):
    from nurb import db

    conn = db.connect()
    project_id = db.create_project(conn, "turns")
    conn.close()

    with serving(home, free_port()) as url:
        route = f"{url}/api/projects/{project_id}/messages"
        # A photo alone is a legitimate message, so no words is fine with a file.
        assert post(route, {"role": "user", "content": "", "files": ["hook.jpg"]})[0] == 201
        assert post(route, {"role": "user", "content": "taller"})[0] == 201

        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        assert [(m["content"], m["files"]) for m in detail["messages"]] == [
            ("", ["hook.jpg"]),
            ("taller", []),
        ]

        with pytest.raises(urllib.error.HTTPError) as not_names:
            post(route, {"role": "user", "content": "hi", "files": "hook.jpg"})
        assert not_names.value.code == 400


def test_a_part_file_from_a_folder_is_captured_as_a_revision(home):
    from nurb import db

    project_id, part_id = a_slab()
    changed = SLAB.replace("width=100.0", "width=140.0")
    with serving(home, free_port()) as url:
        before = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        first = next(p for p in before["parts"] if p["name"] == "slab")

        written = json.loads(
            post(
                f"{url}/api/projects/{project_id}/parts/slab/source",
                {"source": changed, "note": "from the folder"},
            )[2]
        )
        assert written["changed"] is True
        assert written["status"] == "ok"

        conn = db.connect()
        try:
            rows = conn.execute(
                "SELECT * FROM part_revisions WHERE part_id = ? ORDER BY created_at", (part_id,)
            ).fetchall()
            assert len(rows) == 2
            assert rows[-1]["parent_id"] == first["revision_id"]
            assert rows[-1]["source"] == changed
            assert rows[-1]["note"] == "from the folder"
            run = conn.execute(
                "SELECT * FROM build_runs WHERE revision_id = ?", (rows[-1]["id"],)
            ).fetchone()
            assert run["status"] == "ok"
        finally:
            conn.close()

        # The same source again is a no-op, not a revision.
        same = json.loads(
            post(f"{url}/api/projects/{project_id}/parts/slab/source", {"source": changed})[2]
        )
        assert same["changed"] is False
        conn = db.connect()
        try:
            assert conn.execute(
                "SELECT COUNT(*) FROM part_revisions WHERE part_id = ?", (part_id,)
            ).fetchone()[0] == 2
        finally:
            conn.close()


def test_a_saved_port_outside_the_range_is_forgotten(tmp_path):
    from nurb import serve

    # A hand-edited or truncated connect.json must fall back to the port walk, not
    # reach socket.bind, which raises OverflowError for a port above 65535.
    (tmp_path / serve.CONNECT).write_text('{"token": "t", "port": 99999}')
    saved = serve.read_connect(tmp_path)
    assert saved["port"] is None
    assert saved["token"] == "t"
    (tmp_path / serve.CONNECT).write_text('{"token": "t", "port": true}')
    assert serve.read_connect(tmp_path)["port"] is None


def a_container_and_two_folders():
    """One invisible container holding one part, and two folders that hold their own."""
    from nurb import db

    conn = db.connect()
    container = db.create_project(conn, "drab flange 1")
    part_id = db.create_part(conn, container, "hook", SLAB.replace("slab", "hook"))
    shelves = db.create_project(conn, "shelves", folder=True)
    shelf_id = db.create_part(conn, shelves, "shelf", SLAB.replace("slab", "shelf"))
    spares = db.create_project(conn, "spares", folder=True)
    db.create_part(conn, spares, "shelf", SLAB.replace("slab", "shelf"))
    conn.close()
    return container, part_id, shelves, shelf_id, spares


def test_the_part_is_the_unit(home):
    from nurb import db

    container, part_id, shelves, shelf_id, spares = a_container_and_two_folders()
    conn = db.connect()
    alone = db.create_project(conn, "alone")
    alone_part = db.create_part(conn, alone, "peg", SLAB.replace("slab", "peg"))
    conn.close()
    with serving(home, free_port()) as url:
        listed = {row["id"]: row for row in json.loads(get(f"{url}/api/projects")[2])["projects"]}
        assert listed[container]["folder"] is False
        assert listed[shelves]["folder"] is True
        assert json.loads(get(f"{url}/api/projects/{container}")[2])["folder"] is False

        # A new project is a container unless it says otherwise.
        made = json.loads(post(f"{url}/api/projects", {"name": "one part"})[2])
        assert made["folder"] is False
        asked = json.loads(post(f"{url}/api/projects", {"name": "a folder", "folder": True})[2])
        assert asked["folder"] is True

        # A turn of the chat says which part it was about, and can be read back alone.
        about = json.loads(
            post(f"{url}/api/projects/{container}/messages", {"role": "user", "content": "taller", "part": "hook"})[2]
        )
        assert about["part"] == "hook"
        loose = json.loads(
            post(f"{url}/api/projects/{container}/messages", {"role": "user", "content": "hello"})[2]
        )
        assert loose["part"] is None
        whole = json.loads(get(f"{url}/api/projects/{container}")[2])["messages"]
        assert [m["content"] for m in whole] == ["taller", "hello"]
        only = json.loads(get(f"{url}/api/projects/{container}?part=hook")[2])["messages"]
        assert [m["content"] for m in only] == ["taller"]

        with pytest.raises(urllib.error.HTTPError) as unknown:
            post(f"{url}/api/projects/{container}/messages", {"role": "user", "content": "x", "part": "nope"})
        assert unknown.value.code == 400
        assert json.loads(unknown.value.read())["error"] == "no part called nope in this project"

        # Every part in the store, which is what the library's one grid draws.
        library = json.loads(get(f"{url}/api/parts")[2])["parts"]
        assert {(p["name"], p["project_id"], p["project_name"], p["folder"]) for p in library} == {
            ("hook", container, "drab flange 1", False),
            ("shelf", shelves, "shelves", True),
            ("shelf", spares, "spares", True),
            ("peg", alone, "alone", False),
        }
        hook = next(p for p in library if p["id"] == part_id)
        assert hook["revision"] == 1 and hook["build"] is None
        assert hook["source"].startswith("from nurb import *")

        # The container becomes a folder the moment it is worth naming.
        promoted = json.loads(post(f"{url}/api/projects/{container}/folder", {"name": "Hooks"})[2])
        assert (promoted["id"], promoted["name"], promoted["folder"]) == (container, "Hooks", True)

        moved = json.loads(post(f"{url}/api/parts/{part_id}/project", {"project_id": shelves})[2])
        assert moved == {"id": part_id, "project_id": shelves}
        after = json.loads(get(f"{url}/api/projects/{shelves}")[2])
        assert sorted(p["name"] for p in after["parts"]) == ["hook", "shelf"]
        assert [m["content"] for m in after["messages"]] == ["taller"]

        with pytest.raises(urllib.error.HTTPError) as taken:
            post(f"{url}/api/parts/{shelf_id}/project", {"project_id": spares})
        assert taken.value.code == 409
        assert "already has a part called shelf" in json.loads(taken.value.read())["error"]

        with pytest.raises(urllib.error.HTTPError) as nopart:
            post(f"{url}/api/parts/nosuchpart/project", {"project_id": spares})
        assert nopart.value.code == 404
        with pytest.raises(urllib.error.HTTPError) as noproject:
            post(f"{url}/api/parts/{shelf_id}/project", {"project_id": "nosuchproject"})
        assert noproject.value.code == 404

        # Deleting a part in a folder leaves the folder; the folder is the user's.
        gone = json.loads(delete(f"{url}/api/parts/{shelf_id}")[2])
        assert gone == {"deleted": shelf_id, "project_id": shelves, "project_deleted": False}
        assert [p["name"] for p in json.loads(get(f"{url}/api/projects/{shelves}")[2])["parts"]] == ["hook"]

        # A part alone in its container takes the invisible container with it.
        gone = json.loads(delete(f"{url}/api/parts/{alone_part}")[2])
        assert gone == {"deleted": alone_part, "project_id": alone, "project_deleted": True}
        assert alone not in {row["id"] for row in json.loads(get(f"{url}/api/projects")[2])["projects"]}

        with pytest.raises(urllib.error.HTTPError) as nopart:
            delete(f"{url}/api/parts/{alone_part}")
        assert nopart.value.code == 404


def test_the_workshop_holds_the_printers_and_names_the_default(home):
    """A printer is a fact about the workshop, so it is added once and every project
    with no printer.toml of its own prints on it."""
    project_id, _ = a_slab()
    with serving(home, free_port()) as url:
        empty = json.loads(get(f"{url}/api/printers")[2])
        assert empty["printers"] == []
        assert len(empty["catalogue"]) == 16
        first = empty["catalogue"][0]
        assert first["name"] == "bambu_x1c"
        assert first["label"] == "Bambu Lab X1 Carbon"
        assert first["brand"] == "Bambu Lab"
        assert len(first["bed"]) == 3
        # Brands come out grouped, because that is the order the file lists them in.
        brands = [entry["brand"] for entry in empty["catalogue"]]
        assert brands == sorted(brands, key=brands.index)

        added = json.loads(post(f"{url}/api/printers", {"profile": "bambu_p1s"})[2])
        assert [p["name"] for p in added["printers"]] == ["bambu_p1s"]
        assert added["printers"][0]["default"] is True
        assert added["printers"][0]["label"] == "Bambu Lab P1S"

        two = json.loads(post(f"{url}/api/printers", {"profile": "prusa_mk4s"})[2])
        assert [p["name"] for p in two["printers"]] == ["bambu_p1s", "prusa_mk4s"]
        assert [p["default"] for p in two["printers"]] == [True, False]

        # The project never named a machine, so it prints on the workshop's.
        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        assert detail["printer"]["name"] == "bambu_p1s"
        assert detail["printers"] == ["bambu_p1s", "prusa_mk4s"]

        moved = json.loads(post(f"{url}/api/printers/default", {"profile": "prusa_mk4s"})[2])
        assert [p["name"] for p in moved["printers"]] == ["prusa_mk4s", "bambu_p1s"]
        assert moved["printers"][0]["default"] is True

        gone = json.loads(delete(f"{url}/api/printers/prusa_mk4s")[2])
        assert [p["name"] for p in gone["printers"]] == ["bambu_p1s"]
        assert gone["printers"][0]["default"] is True

        # A project may still disagree, and may go back to the workshop's answer.
        named = json.loads(
            post(f"{url}/api/projects/{project_id}/printer", {"profile": "prusa_xl"})[2]
        )
        assert named["printer"]["name"] == "prusa_xl"
        cleared = json.loads(
            post(f"{url}/api/projects/{project_id}/printer", {"profile": None})[2]
        )
        assert cleared["printer"]["name"] == "bambu_p1s"

        # Taking a machine off the bench takes it off every project that named it.
        post(f"{url}/api/printers", {"profile": "prusa_xl"})
        post(f"{url}/api/projects/{project_id}/printer", {"profile": "prusa_xl"})
        delete(f"{url}/api/printers/prusa_xl")
        detail = json.loads(get(f"{url}/api/projects/{project_id}")[2])
        assert detail["printer"]["name"] == "bambu_p1s"
        assert detail["printers"] == ["bambu_p1s"]

        with pytest.raises(urllib.error.HTTPError) as unknown:
            post(f"{url}/api/printers", {"profile": "nosuchprinter"})
        assert unknown.value.code == 400
        assert "bambu_p1s" in json.loads(unknown.value.read())["error"]

        with pytest.raises(urllib.error.HTTPError) as absent:
            delete(f"{url}/api/printers/prusa_mk4s")
        assert absent.value.code == 404

        with pytest.raises(urllib.error.HTTPError) as unowned:
            post(f"{url}/api/printers/default", {"profile": "prusa_mk4s"})
        assert unowned.value.code == 400
        assert "Add it first" in json.loads(unowned.value.read())["error"]


def test_unbuilt_parts_build_in_the_background_after_an_import(tmp_path, monkeypatch):
    """A library an import just filled gets its pictures without anyone opening a part."""
    import threading
    import time

    import shutil

    from nurb import db, folder, serve

    monkeypatch.setenv("NURB_HOME", str(tmp_path))
    conn = db.connect()
    project = tmp_path / "shop"
    shutil.copytree(pathlib.Path(__file__).parents[1] / "examples" / "demo", project)
    # A shared module is source the parts import, never something to build on its own.
    (project / "system.py").write_text("WALL = 2.0\n", encoding="utf-8")
    project_id, count = folder.import_folder(conn, project)
    first = serve.next_unbuilt(conn)
    assert first is not None
    assert serve.next_unbuilt(conn, skip=[first[1]]) != first

    wake, stop = threading.Event(), threading.Event()
    wake.set()
    worker = threading.Thread(target=serve.build_unbuilt, args=(wake, stop), daemon=True)
    worker.start()
    deadline = time.monotonic() + 240
    while serve.next_unbuilt(conn) is not None and time.monotonic() < deadline:
        time.sleep(0.5)
    stop.set()
    wake.set()
    worker.join(timeout=30)

    assert serve.next_unbuilt(conn) is None
    built = conn.execute(
        "SELECT COUNT(*) FROM parts JOIN build_runs ON build_runs.revision_id = parts.current_revision_id"
        " WHERE parts.project_id = ? AND parts.kind = 'part'",
        (project_id,),
    ).fetchone()[0]
    assert built == count
    modules = conn.execute(
        "SELECT COUNT(*) FROM parts JOIN build_runs ON build_runs.revision_id = parts.current_revision_id"
        " WHERE parts.kind = 'module'"
    ).fetchone()[0]
    assert modules == 0
    conn.close()


def test_library_thumbnail_is_one_view_on_a_transparent_ground(tmp_path, monkeypatch):
    """The card's picture is the part alone, so the card's own ground shows through."""
    import io

    from PIL import Image
    from starlette.testclient import TestClient

    from nurb import db, engine_run, folder, serve

    monkeypatch.setenv("NURB_HOME", str(tmp_path))
    conn = db.connect(check_same_thread=False)
    project_id, _ = folder.import_folder(conn, pathlib.Path(__file__).parents[1] / "examples" / "demo")
    part = conn.execute("SELECT id, name FROM parts WHERE kind = 'part'").fetchone()
    run_id, _ = engine_run.run_build(conn, part["id"])
    serve.THUMBNAILS.clear()

    from starlette.applications import Starlette

    _, routes, _ = serve._routes(conn, __import__("threading").Lock(), None, "t", 0)
    client = TestClient(Starlette(routes=[r for r in routes if getattr(r, "path", "").startswith("/thumbnail")]))
    response = client.get(f"/thumbnail/{project_id}/{part['name']}.png?run={run_id}")
    assert response.status_code == 200
    image = Image.open(io.BytesIO(response.content))
    assert image.mode == "RGBA" and image.size == (640, 480)
    assert image.getpixel((0, 0))[3] == 0
    assert run_id in serve.THUMBNAILS
    assert client.get(f"/thumbnail/{project_id}/{part['name']}.png?run=nope").status_code == 404
    conn.close()


def test_the_project_panel_reads_and_tunes_the_system(tmp_path, monkeypatch):
    """Settings are the plain numbers in a shared file, pieces are its functions, and
    changing either a setting or a measurement queues the parts that use it."""
    import threading

    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    from nurb import db, engine_run, serve

    monkeypatch.setenv("NURB_HOME", str(tmp_path))
    conn = db.connect(check_same_thread=False)
    project_id = db.create_project(conn, "shelf", folder=True)
    db.create_part(
        conn, project_id, "system",
        'from nurb import *\nWALL = 2.0  # every wall\nCOUNT = 3\n_EPS = 1e-4\nDERIVED = WALL * 2\n\n'
        'def slab(w):\n    return Box(w, w, WALL)\n',
        kind="module",
    )
    db.set_measurement(conn, project_id, "rail_width", 20.0, "calipers")
    db.create_part(conn, project_id, "bin_a", 'from nurb import *\nfrom system import slab\n\n@part\ndef bin_a(w=20.0):\n    return slab(w)\n')
    db.create_part(conn, project_id, "lid", 'from nurb import *\nimport system\n\n@part\ndef lid(w=measured("rail_width")):\n    return Box(w, w, 1)\n')
    while engine_run.take_rebuild():
        pass
    _, routes, _ = serve._routes(conn, threading.Lock(), None, "t", 0)
    client = TestClient(Starlette(routes=[r for r in routes if "/api/projects" in getattr(r, "path", "")]))

    system = client.get(f"/api/projects/{project_id}/system").json()
    [file] = system["files"]
    assert file["used_by"] == ["bin_a", "lid"]
    assert [(s["name"], s["value"], s["kind"], s["note"]) for s in file["settings"]] == [
        ("WALL", 2.0, "float", "every wall"),
        ("COUNT", 3, "int", ""),
    ]
    assert file["pieces"] == [{"name": "slab", "used_by": ["bin_a"]}]
    assert system["measurements"][0]["used_by"] == ["lid"]

    assert "whole number" in client.post(
        f"/api/projects/{project_id}/settings", json={"file": "system", "name": "COUNT", "value": 2.5}
    ).json()["error"]
    after = client.post(f"/api/projects/{project_id}/settings", json={"file": "system", "name": "WALL", "value": 3.0}).json()
    assert after["files"][0]["settings"][0]["value"] == 3.0
    queued = {engine_run.take_rebuild(), engine_run.take_rebuild()}
    assert len(queued - {None}) == 2 and engine_run.take_rebuild() is None

    fixed = client.patch(f"/api/projects/{project_id}/measurements/rail_width", json={"value_mm": 21.5}).json()
    assert fixed["measurements"][0]["value_mm"] == 21.5
    names = {r["id"]: r["name"] for r in db.parts_of(conn, project_id)}
    assert names[engine_run.take_rebuild()] == "lid" and engine_run.take_rebuild() is None
    conn.close()


def test_a_build_that_hits_a_locked_database_is_tried_again(tmp_path, monkeypatch):
    """An import holding the write lock past the busy timeout must not leave a part
    on Not built yet until restart (#291)."""
    import sqlite3
    import threading
    import time

    from nurb import db, engine_run, serve

    monkeypatch.setenv("NURB_HOME", str(tmp_path))
    conn = db.connect()
    project_id = db.create_project(conn, "shop")
    db.create_part(conn, project_id, "cube", "from nurb import *\n\n@part\ndef cube(size=10.0):\n    return Box(size, size, size)\n")

    holder = sqlite3.connect(tmp_path / "scratch.db", autocommit=True)
    waiter = sqlite3.connect(tmp_path / "scratch.db", autocommit=True, timeout=0)
    holder.execute("BEGIN IMMEDIATE")
    try:
        waiter.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as exc:
        locked = exc
    holder.close()
    waiter.close()

    real_run_build = engine_run.run_build
    calls = []

    def run_build(conn, part_id, **kwargs):
        calls.append(part_id)
        if len(calls) == 1:
            raise locked
        return real_run_build(conn, part_id, **kwargs)

    monkeypatch.setattr(engine_run, "run_build", run_build)
    wake, stop = threading.Event(), threading.Event()
    wake.set()
    worker = threading.Thread(target=serve.build_unbuilt, args=(wake, stop), daemon=True)
    worker.start()
    deadline = time.monotonic() + 120
    while serve.next_unbuilt(conn) is not None and time.monotonic() < deadline:
        time.sleep(0.2)
    stop.set()
    wake.set()
    worker.join(timeout=30)

    assert len(calls) == 2
    assert serve.next_unbuilt(conn) is None


def test_a_3mf_downloads_when_the_slicer_lacks_the_printer(home):
    """The slicer's reason runs to several lines, and a header holds only one (#301)."""
    project_id, part_id = a_slab()
    with serving(home, free_port()) as url:
        post(f"{url}/api/projects/{project_id}/printer", {"profile": "prusa_mk4s"})
        status, headers, body = post(f"{url}/api/parts/{part_id}/export", {"format": "3mf"})
        assert status == 200
        assert body[:2] == b"PK"
        assert headers["X-Nurb-Print-Settings"]
