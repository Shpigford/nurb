"""Labels: a person's names for spots on a part, and what a rebuild does to them."""

import json
import threading

import pytest

from nurb import db, mcp_server

BASE = "http://127.0.0.1:7373"

CUBE = """from nurb import *


@part
def cube(width=20.0):
    return Box(width, width, width)
"""


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    conn = db.connect(tmp_path / "x.db", check_same_thread=False)
    yield conn
    conn.close()


def call(conn, name, args):
    return mcp_server.dispatch(conn, name, args, BASE)


def payload(result):
    assert result.is_error is False, result.content[0].text
    return json.loads(result.content[0].text)


def a_cube(conn):
    project_id = db.create_project(conn, "cubes")
    payload(call(conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE}))
    return project_id


def test_a_label_snaps_to_the_surface_and_names_the_way_it_faces(conn):
    project_id = a_cube(conn)
    # Two mm above the top face of a 20 mm cube centred on the origin.
    said = payload(call(conn, "set_label", {"project_id": project_id, "part_name": "cube", "name": "lid", "point": [0, 0, 12]}))
    assert said["point"] == [0, 0, 10]
    assert said["facing"] == "up"
    assert said["moved_to_surface_mm"] == 2.0

    [part] = payload(call(conn, "get_project", {"project_id": project_id}))["parts"]
    [label] = part["labels"]
    assert (label["name"], label["on_part"], label["off_mm"]) == ("lid", True, 0.0)
    assert "labels_off_note" not in part


def test_a_part_without_labels_says_nothing_about_them(conn):
    project_id = a_cube(conn)
    [part] = payload(call(conn, "get_project", {"project_id": project_id}))["parts"]
    assert "labels" not in part and "labels_note" not in part


def test_an_edit_that_moves_the_surface_away_flags_the_label(conn):
    project_id = a_cube(conn)
    payload(call(conn, "set_label", {"project_id": project_id, "part_name": "cube", "name": "lid", "point": [0, 0, 10]}))
    built = payload(call(conn, "edit_part_source", {
        "project_id": project_id, "part_name": "cube", "old_string": "width=20.0", "new_string": "width=10.0",
    }))
    [label] = built["labels"]
    assert label["on_part"] is False and label["off_mm"] == 5.0
    assert "lid" in built["labels_off_note"]

    # Moved onto the new top, it means the lid again.
    payload(call(conn, "set_label", {"project_id": project_id, "part_name": "cube", "name": "lid", "point": [0, 0, 5]}))
    [part] = payload(call(conn, "get_project", {"project_id": project_id}))["parts"]
    assert [(l["name"], l["on_part"]) for l in part["labels"]] == [("lid", True)]


def test_a_part_that_never_built_cannot_be_labelled(conn):
    project_id = db.create_project(conn, "cubes")
    db.create_part(conn, project_id, "cube", CUBE)
    result = call(conn, "set_label", {"project_id": project_id, "part_name": "cube", "name": "lid", "point": [0, 0, 10]})
    assert result.is_error and "not built yet" in result.content[0].text


def test_deleting_a_label_that_is_not_there_says_so(conn):
    project_id = a_cube(conn)
    result = call(conn, "delete_label", {"project_id": project_id, "part_name": "cube", "name": "lid"})
    assert result.is_error and "no label called lid" in result.content[0].text


def test_the_workbench_names_renames_and_removes_a_spot(conn):
    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    from nurb import serve

    project_id = a_cube(conn)
    part_id = db.parts_of(conn, project_id)[0]["id"]
    _, routes, _ = serve._routes(conn, threading.Lock(), None, "t", 0)
    client = TestClient(Starlette(routes=[r for r in routes if getattr(r, "path", "").startswith("/api/")]))

    def shown():
        return client.get(f"/api/projects/{project_id}").json()["parts"][0]["labels"]

    assert client.post(f"/api/parts/{part_id}/labels", json={"name": " Front ", "point": [0, -10, 0]}).status_code == 200
    [label] = shown()
    assert (label["name"], label["facing"], label["on_part"]) == ("Front", "-Y", True)

    refused = client.post(f"/api/parts/{part_id}/labels", json={"name": "x", "point": [0, 0]})
    assert refused.status_code == 400 and "three numbers" in refused.json()["error"]

    client.post(f"/api/parts/{part_id}/labels", json={"name": "Top", "point": [0, 0, 10]})
    taken = client.patch(f"/api/parts/{part_id}/labels/Front", json={"name": "Top"})
    assert taken.status_code == 400 and "already has a label called Top" in taken.json()["error"]
    assert client.patch(f"/api/parts/{part_id}/labels/Front", json={"name": "Face"}).status_code == 200
    assert [l["name"] for l in shown()] == ["Face", "Top"]

    assert client.delete(f"/api/parts/{part_id}/labels/Face").status_code == 200
    assert [l["name"] for l in shown()] == ["Top"]
    assert client.delete(f"/api/parts/{part_id}/labels/Face").status_code == 404


def test_labels_go_with_their_part(conn):
    project_id = a_cube(conn)
    part_id = db.parts_of(conn, project_id)[0]["id"]
    payload(call(conn, "set_label", {"project_id": project_id, "part_name": "cube", "name": "lid", "point": [0, 0, 10]}))
    db.delete_part(conn, part_id)
    assert conn.execute("SELECT COUNT(*) FROM labels").fetchone()[0] == 0


def test_a_name_with_a_slash_can_be_renamed_and_removed(conn):
    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    from nurb import serve

    project_id = a_cube(conn)
    part_id = db.parts_of(conn, project_id)[0]["id"]
    _, routes, _ = serve._routes(conn, threading.Lock(), None, "t", 0)
    client = TestClient(Starlette(routes=[r for r in routes if getattr(r, "path", "").startswith("/api/")]))
    client.post(f"/api/parts/{part_id}/labels", json={"name": "1/4 hole", "point": [0, 0, 10]})
    assert client.patch(f"/api/parts/{part_id}/labels/1%2F4%20hole", json={"name": "3/8 hole"}).status_code == 200
    assert client.delete(f"/api/parts/{part_id}/labels/3%2F8%20hole").status_code == 200
    assert db.labels_of(conn, part_id) == []


def test_the_library_read_does_not_measure_labels(conn, monkeypatch):
    from nurb import labels, serve

    project_id = a_cube(conn)
    payload(call(conn, "set_label", {"project_id": project_id, "part_name": "cube", "name": "lid", "point": [0, 0, 10]}))
    monkeypatch.setattr(labels, "placed", lambda *a: pytest.fail("the library read measured labels"))
    serve._all_parts(conn)
