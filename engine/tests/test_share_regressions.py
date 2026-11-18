"""Sharing preserves one build and everything needed to reopen it."""

import concurrent.futures
import io
import json
import threading
import xml.etree.ElementTree as ET
import zipfile

import pytest
import trimesh
from starlette.applications import Starlette
from starlette.testclient import TestClient

from nurb import db, engine_run, mcp_server, serve, share
from test_serve import home


@pytest.fixture
def library(home):
    conn = db.connect(check_same_thread=False)
    project = db.create_project(conn, "shared")
    yield conn, project
    conn.close()


def build(conn, project, name):
    row = next(row for row in db.parts_of(conn, project) if row["name"] == name)
    run_id, result = engine_run.run_build(conn, row["id"])
    assert result["error"] is None
    return row, conn.execute("SELECT * FROM build_runs WHERE id = ?", (run_id,)).fetchone()


@pytest.mark.parametrize("decorator,default", [("part", "WIDTH"), ("assembly", "10.0")])
def test_the_copy_reopens_at_the_shared_slider_values(library, decorator, default):
    conn, project = library
    db.create_part(conn, project, "system", "WIDTH = 10.0\n", kind="module")
    source = f"from nurb import *\nfrom system import WIDTH\n@{decorator}\ndef slab(width={default}):\n    return Box(width, 10, 2)\n"
    db.create_part(conn, project, "slab", source)
    row, run = build(conn, project, "slab")
    opened, _ = share.land(conn, share.bundle(conn, row, run, {"width": 30.123456789}))
    _, copied = build(conn, opened, "slab")
    assert json.loads(copied["stats"])["bbox"] == [30.12, 10, 2]
    assert json.loads(copied["params"])[0]["default"] == 30.123456789


def test_supporting_files_and_provisional_measurements_survive_the_copy(library):
    conn, project = library
    db.add_project_file(conn, project, "helpers/__init__.py", b"DEPTH = 12.0\n")
    db.add_project_file(conn, project, "assets/height.txt", b"2.0")
    db.set_measurement(conn, project, "width", 25, "eyeballed", provisional=True)
    db.create_part(conn, project, "slab", '''from nurb import *
from pathlib import Path
from helpers import DEPTH
@part
def slab():
    height = float((Path(__file__).parent.parent / "assets/height.txt").read_text())
    return Box(measured("width"), DEPTH, height)
''')
    row, run = build(conn, project, "slab")
    opened, _ = share.land(conn, share.bundle(conn, row, run, {}))
    _, copied = build(conn, opened, "slab")
    assert json.loads(copied["stats"])["bbox"] == [25, 12, 2]
    assert db.measurements_of(conn, opened)[0]["provisional"] == 1
    assert {r["path"]: r["content"] for r in db.project_files_of(conn, opened)} == {
        "helpers/__init__.py": b"DEPTH = 12.0\n", "assets/height.txt": b"2.0",
    }


def client_for(conn):
    lock = threading.Lock()
    server = mcp_server.make_server(conn, "http://localhost", lock=lock)
    _, routes, _ = serve._routes(conn, lock, server, "test", 1)
    return TestClient(Starlette(routes=routes), raise_server_exceptions=False)


def test_a_frozen_measurement_default_keeps_its_provisional_status(library):
    conn, project = library
    db.set_measurement(conn, project, "width", 10, "eyeballed", provisional=True)
    db.create_part(conn, project, "slab", 'from nurb import *\n@part\ndef slab(width=measured("width")):\n    return Box(width,10,2)\n')
    row, run = build(conn, project, "slab")
    opened, _ = share.land(conn, share.bundle(conn, row, run, {"width": 20.0}))
    assert db.measurements_of(conn, opened)[0]["provisional"] == 1
    _, copy = build(conn, opened, "slab")
    assert json.loads(copy["stats"])["bbox"][0] == 20


@pytest.mark.parametrize("files", [
    [{"path": "../escape", "content": "eA=="}],
    [{"path": "/escape", "content": "eA=="}],
    [{"path": "helpers/x.py", "content": "not base64"}],
    [{"path": "helpers", "content": "eA=="}, {"path": "helpers/x.py", "content": "eA=="}],
    [{"path": "helpers/x.py", "content": "eA=="}] * 2,
])
def test_bad_supporting_files_leave_no_partial_copy(library, files):
    conn, _ = library
    before = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    with pytest.raises(share.ShareError):
        share.land(conn, {"format": 1, "name": "slab", "source": "", "files": files})
    assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == before


@pytest.mark.parametrize("whole_project", [False, True])
def test_deletion_waits_for_the_upload_token_and_takes_the_link_down(library, monkeypatch, whole_project):
    conn, project = library
    part = db.create_part(conn, project, "slab", "from nurb import *\n@part\ndef slab():\n    return Box(10,10,2)\n")
    build(conn, project, "slab")
    uploaded, release = threading.Event(), threading.Event()
    public = {}

    def upload(files, existing):
        public["Abcde12345"] = "secret"
        uploaded.set()
        assert release.wait(10)
        return {"id": "Abcde12345", "token": "secret"}

    def remove(row):
        assert public.pop(row["share_id"]) == row["token"]

    monkeypatch.setattr(share, "upload", upload)
    monkeypatch.setattr(share, "remove", remove)
    target = f"/api/projects/{project}" if whole_project else f"/api/parts/{part}"
    with client_for(conn) as client, concurrent.futures.ThreadPoolExecutor() as pool:
        sharing = pool.submit(client.post, f"/api/parts/{part}/share", json={"values": {}})
        try:
            assert uploaded.wait(20)
            deleting = pool.submit(client.delete, target)
            with pytest.raises(concurrent.futures.TimeoutError):
                deleting.result(timeout=0.2)
        finally:
            release.set()
        assert sharing.result(timeout=10).status_code == 200
        assert deleting.result(timeout=10).status_code == 200
    assert not public
    assert conn.execute("SELECT COUNT(*) FROM shares").fetchone()[0] == 0


def test_all_shared_files_use_the_snapshot_even_when_source_changes(library, monkeypatch):
    conn, project = library
    source = "from nurb import *\n@part\ndef slab():\n    return Box(10,10,2)\n"
    part = db.create_part(conn, project, "slab", source)
    build(conn, project, "slab")
    original = engine_run.export_geometry
    captured = {}

    def export(*args, **kwargs):
        result = original(*args, **kwargs)
        if args[1] == "stl":
            db.add_revision(conn, part, source.replace("Box(10,", "Box(20,"))
        return result

    def upload(files, existing):
        captured.update(files)
        return {"id": "Abcde12345", "token": "secret"}

    monkeypatch.setattr(engine_run, "export_geometry", export)
    monkeypatch.setattr(share, "upload", upload)
    with client_for(conn) as client:
        response = client.post(f"/api/parts/{part}/share", json={"values": {}})
    assert response.status_code == 200, response.text
    stl = trimesh.load(io.BytesIO(captured["part.stl"]), file_type="stl")
    glb = trimesh.load(io.BytesIO(captured["part.glb"]), file_type="glb")
    xs = []
    with zipfile.ZipFile(io.BytesIO(captured["part.3mf"])) as archive:
        for name in archive.namelist():
            if name.endswith(".model"):
                model = ET.fromstring(archive.read(name))
                xs.extend(float(v.attrib["x"]) for v in model.iter() if v.tag.split("}")[-1] == "vertex")
    assert stl.extents[0] == pytest.approx(10)
    assert glb.extents[0] == pytest.approx(10)
    assert max(xs) - min(xs) == pytest.approx(10)
    copied, _ = share.land(conn, json.loads(captured["part.json"]))
    _, run = build(conn, copied, "slab")
    assert json.loads(run["stats"])["bbox"][0] == pytest.approx(10)
