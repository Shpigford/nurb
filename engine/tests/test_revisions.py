"""A part's history: every revision listed, an old one looked at, and one brought back."""

import json
import threading

import pytest

from nurb import db, engine_run, mcp_server

BASE = "http://127.0.0.1:7373"


def cube(width, name="cube"):
    return f"from nurb import *\n\n\n@part\ndef {name}(width={width}):\n    return Box(width, width, width)\n"


BROKEN = "from nurb import *\n\n\n@part\ndef cube(width=20.0):\n    return Box(width, width)\n"


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


def write(conn, project_id, source, name="cube"):
    payload(call(conn, "write_part_source", {"project_id": project_id, "part_name": name, "source": source}))


@pytest.fixture
def history(conn):
    """A cube at 10, then 20, then a revision that does not build, then 30."""
    project_id = db.create_project(conn, "cubes")
    write(conn, project_id, cube(10.0))
    write(conn, project_id, cube(20.0))
    result = call(conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": BROKEN})
    assert "error" in result.content[0].text
    write(conn, project_id, cube(30.0))
    part_id = db.parts_of(conn, project_id)[0]["id"]
    return project_id, part_id


@pytest.fixture
def client(conn):
    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    from nurb import serve

    _, routes, _ = serve._routes(conn, threading.Lock(), None, "t", 0)
    keep = ("/api/", "/glb/", "/render/")
    return TestClient(Starlette(routes=[r for r in routes if getattr(r, "path", "").startswith(keep)]))


def runs(conn):
    return conn.execute("SELECT COUNT(*) FROM build_runs").fetchone()[0]


def test_the_history_lists_every_revision_newest_first(conn, history, client):
    _, part_id = history
    listed = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"]
    assert [r["revision"] for r in listed] == [4, 3, 2, 1]
    assert [r["status"] for r in listed] == ["ok", "error", "ok", "ok"]
    assert [r["current"] for r in listed] == [True, False, False, False]
    assert listed[1]["thumbnail_url"] is None
    assert listed[2]["thumbnail_url"].startswith("/thumbnail/")


def test_looking_back_shows_that_revision_and_builds_nothing(conn, history, client):
    project_id, part_id = history
    before = runs(conn)
    current = db.parts_of(conn, project_id)[0]["current_revision_id"]
    rev2 = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"][2]
    view = client.get(f"/api/parts/{part_id}/revisions/{rev2['id']}").json()
    assert view["revision"] == 2 and view["status"] == "ok" and not view["current"]
    assert "width=20.0" in view["source"]
    assert [(p["name"], p["value"]) for p in view["params"]] == [("width", 20.0)]
    # The same shape as a part's own build, so the page draws it with the same code.
    assert view["build"]["status"] == "ok" and view["build"]["stale"] is False and view["build"]["shown_revision"] == 2
    assert view["build"]["stats"]["bbox"] == pytest.approx([20.0, 20.0, 20.0])

    # The URL names rev 2's run and serves rev 2's bytes, not the newest build's.
    glb = client.get(view["build"]["glb_url"])
    assert glb.status_code == 200
    stored = conn.execute("SELECT glb FROM build_runs WHERE id = ?", (view["build"]["id"],)).fetchone()["glb"]
    assert glb.content == stored
    newest = client.get(f"/glb/{project_id}/cube.glb")
    assert newest.content != stored
    assert client.get(view["build"]["render_url"]).status_code == 200

    assert runs(conn) == before
    assert db.parts_of(conn, project_id)[0]["current_revision_id"] == current


def test_a_revision_that_did_not_build_says_why_and_shows_nothing_else(conn, history, client):
    _, part_id = history
    rev3 = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"][1]
    view = client.get(f"/api/parts/{part_id}/revisions/{rev3['id']}").json()
    assert view["status"] == "error" and view["build"] is None
    assert view["error"]


def test_a_run_url_never_falls_back_to_another_run(conn, history, client):
    project_id, part_id = history
    assert client.get(f"/glb/{project_id}/cube.glb?run=nope").status_code == 404
    assert client.get(f"/render/{project_id}/cube.png?run=nope").status_code == 404
    other = db.create_project(conn, "other")
    write(conn, other, cube(5.0))
    foreign = db.latest_ok_run(conn, db.parts_of(conn, other)[0]["id"])["id"]
    assert client.get(f"/glb/{project_id}/cube.glb?run={foreign}").status_code == 404


def test_another_parts_revision_is_not_this_parts(conn, history, client):
    _, part_id = history
    other = db.create_project(conn, "other")
    write(conn, other, cube(5.0))
    foreign = db.parts_of(conn, other)[0]
    assert client.get(f"/api/parts/{part_id}/revisions/{foreign['current_revision_id']}").status_code == 404
    restore = client.post(f"/api/parts/{part_id}/revisions/{foreign['current_revision_id']}/restore", json={})
    assert restore.status_code == 404


def test_restoring_appends_a_new_revision_and_builds_it(conn, history, client):
    project_id, part_id = history
    listed = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"]
    current, rev1 = listed[0], listed[3]
    answer = client.post(
        f"/api/parts/{part_id}/revisions/{rev1['id']}/restore", json={"expected_revision_id": current["id"]}
    )
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["revision"] == 5 and body["build"]["status"] == "ok"
    assert body["build"]["stats"]["bbox"] == pytest.approx([10.0, 10.0, 10.0])
    row = db.parts_of(conn, project_id)[0]
    assert "width=10.0" in row["source"]
    revision = conn.execute("SELECT * FROM part_revisions WHERE id = ?", (body["revision_id"],)).fetchone()
    assert revision["note"] == "Restored rev 1" and revision["parent_id"] == current["id"]
    # Nothing was rewound: all four earlier revisions are still there.
    assert [r["revision"] for r in client.get(f"/api/parts/{part_id}/revisions").json()["revisions"]] == [5, 4, 3, 2, 1]
    messages = client.get(f"/api/projects/{project_id}").json()["messages"]
    assert messages[-1]["payload"]["type"] == "build"
    # Filed under the part, which is how a folder's per-part conversation finds it.
    assert messages[-1]["part"] == "cube"


def test_a_restore_after_another_edit_landed_is_refused(conn, history, client):
    project_id, part_id = history
    listed = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"]
    seen, rev1 = listed[0]["id"], listed[3]["id"]
    write(conn, project_id, cube(40.0))
    refused = client.post(f"/api/parts/{part_id}/revisions/{rev1}/restore", json={"expected_revision_id": seen})
    assert refused.status_code == 409 and "changed while you were looking" in refused.json()["error"]
    assert "width=40.0" in db.parts_of(conn, project_id)[0]["source"]


def test_restoring_the_current_revision_says_so(conn, history, client):
    _, part_id = history
    current = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"][0]["id"]
    refused = client.post(f"/api/parts/{part_id}/revisions/{current}/restore", json={})
    assert refused.status_code == 400 and "already the current revision" in refused.json()["error"]


def test_a_restore_from_before_a_rename_keeps_the_new_name(conn, history, client):
    project_id, part_id = history
    rev1 = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"][-1]["id"]
    db.rename_part(conn, part_id, "block")
    while engine_run.take_rebuild():
        pass
    answer = client.post(f"/api/parts/{part_id}/revisions/{rev1}/restore", json={})
    assert answer.status_code == 200, answer.text
    assert answer.json()["build"]["status"] == "ok"
    source = db.parts_of(conn, project_id)[0]["source"]
    assert "def block(width=10.0)" in source and "def cube" not in source


def test_restore_carries_the_card_including_none(conn):
    project_id = db.create_project(conn, "cards")
    part_id = db.create_part(conn, project_id, "cube", cube(10.0), card_md="# first")
    first = db.parts_of(conn, project_id)[0]["current_revision_id"]
    db.add_revision(conn, part_id, cube(20.0), card_md=None)
    new = db.restore_revision(conn, part_id, first)
    assert conn.execute("SELECT card_md FROM part_revisions WHERE id = ?", (new,)).fetchone()[0] == "# first"


def test_events_fire_on_restore_and_not_on_reading(conn, history, client):
    project_id, part_id = history
    heard = []
    listen = lambda kind, row_id, project: heard.append((kind, row_id))
    db.listeners.append(listen)
    try:
        listed = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"]
        client.get(f"/api/parts/{part_id}/revisions/{listed[2]['id']}")
        assert heard == []
        db.restore_revision(conn, part_id, listed[2]["id"])
        assert ("part", part_id) in heard
    finally:
        db.listeners.remove(listen)
    # The restored revision is the current one, unbuilt, so the background builder takes it.
    from nurb import serve

    assert serve.next_unbuilt(conn) == (part_id, db.parts_of(conn, project_id)[0]["current_revision_id"])


def test_the_agent_lists_reads_and_restores_by_number(conn, history):
    project_id, _ = history
    listed = payload(call(conn, "list_revisions", {"project_id": project_id, "part_name": "cube"}))
    assert [r["revision"] for r in listed["revisions"]] == [4, 3, 2, 1]
    assert [r["status"] for r in listed["revisions"]] == ["built", "did not build", "built", "built"]
    assert "source" not in listed

    one = payload(call(conn, "list_revisions", {"project_id": project_id, "part_name": "cube", "revision": 2}))
    assert one["source_of"] == 2 and "width=20.0" in one["source"]

    missing = call(conn, "list_revisions", {"project_id": project_id, "part_name": "cube", "revision": 9})
    assert missing.is_error and "no rev 9" in missing.content[0].text

    restored = payload(call(conn, "restore_revision", {"project_id": project_id, "part_name": "cube", "revision": 2}))
    assert restored["status"] == "ok" and restored["restored"] == 2 and restored["revision"] == 5
    assert "width=20.0" in db.parts_of(conn, project_id)[0]["source"]

    same = call(conn, "restore_revision", {"project_id": project_id, "part_name": "cube", "revision": 5})
    assert same.is_error and "already the current revision" in same.content[0].text


def test_a_restore_from_before_a_siblings_rename_opens_it_by_its_new_name(conn, client):
    project_id = db.create_project(conn, "set", folder=True)
    write(conn, project_id, cube(10.0, "bracket"), name="bracket")
    holder = "from nurb import *\n\n\n@assembly\ndef holder(gap={gap}):\n    return Pos(gap, 0, 0) * use(\"bracket\")\n"
    write(conn, project_id, holder.format(gap=0.0), name="holder")
    write(conn, project_id, holder.format(gap=5.0), name="holder")
    parts = {row["name"]: row for row in db.parts_of(conn, project_id)}
    first = conn.execute(
        "SELECT id FROM part_revisions WHERE part_id = ? ORDER BY created_at LIMIT 1", (parts["holder"]["id"],)
    ).fetchone()["id"]
    db.rename_part(conn, parts["bracket"]["id"], "arm")
    while engine_run.take_rebuild():
        pass
    answer = client.post(f"/api/parts/{parts['holder']['id']}/revisions/{first}/restore", json={})
    assert answer.status_code == 200, answer.text
    assert answer.json()["build"]["status"] == "ok", answer.json()["build"]["error"]
    source = {row["name"]: row for row in db.parts_of(conn, project_id)}["holder"]["source"]
    assert 'use("arm")' in source and "gap=0.0" in source


def test_the_rename_fix_takes_the_parts_own_function_not_the_first_decorated_one(conn):
    project_id = db.create_project(conn, "two")
    source = (
        "from nurb import *\n\n\n@part\ndef helper(w=1.0):\n    return Box(w, w, w)\n\n\n"
        "@part\ndef cube(width=10.0):\n    return Box(width, width, width)\n"
    )
    part_id = db.create_part(conn, project_id, "cube", source)
    first = db.parts_of(conn, project_id)[0]["current_revision_id"]
    db.rename_part(conn, part_id, "block")
    new = db.restore_revision(conn, part_id, first)
    restored = conn.execute("SELECT source FROM part_revisions WHERE id = ?", (new,)).fetchone()["source"]
    assert "def helper(" in restored and "def block(width=10.0)" in restored and "def cube" not in restored


def test_a_restore_across_a_swap_of_names_opens_each_part_it_meant(conn):
    """a -> temp, b -> a, temp -> b: what was use("a") is now use("b"), and the reverse.
    Rewriting one rename at a time would turn both into the same part."""
    project_id = db.create_project(conn, "swap", folder=True)
    a = db.create_part(conn, project_id, "a", cube(1.0, "a"))
    b = db.create_part(conn, project_id, "b", cube(2.0, "b"))
    holder = db.create_part(conn, project_id, "h", 'from nurb import *\n\n\n@assembly\ndef h():\n    return use("a"), use("b")\n')
    first = {row["name"]: row for row in db.parts_of(conn, project_id)}["h"]["current_revision_id"]
    db.add_revision(conn, holder, 'from nurb import *\n\n\n@assembly\ndef h():\n    return use("a")\n')
    db.rename_part(conn, a, "temp")
    db.rename_part(conn, b, "a")
    db.rename_part(conn, a, "b")
    new = db.restore_revision(conn, holder, first)
    source = conn.execute("SELECT source FROM part_revisions WHERE id = ?", (new,)).fetchone()["source"]
    assert 'use("b"), use("a")' in source


def test_revisions_written_in_the_same_instant_get_their_own_numbers(conn, history, client):
    """The agent acts on "rev N", so a number has to name one revision. Two saved in
    the same instant are told apart by the order they were written."""
    project_id, part_id = history
    stamp = conn.execute(
        "SELECT created_at FROM part_revisions WHERE part_id = ? ORDER BY created_at LIMIT 1", (part_id,)
    ).fetchone()[0]
    with db.transaction(conn):
        conn.execute(
            "INSERT INTO part_revisions (id, part_id, source, created_at) VALUES ('twin', ?, ?, ?)",
            (part_id, cube(15.0), stamp),
        )
    listed = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"]
    assert [r["revision"] for r in listed] == [5, 4, 3, 2, 1]
    assert {r["id"]: r["revision"] for r in listed}["twin"] == db.revision_ordinal(conn, "twin") == 2
    restored = payload(call(conn, "restore_revision", {"project_id": project_id, "part_name": "cube", "revision": 2}))
    assert restored["restored"] == 2
    assert "width=15.0" in db.parts_of(conn, project_id)[0]["source"]


def test_the_history_groups_revisions_by_the_message_that_asked_for_them(conn, client):
    project_id = db.create_project(conn, "cubes")
    db.add_message(conn, project_id, "user", "a cube", {})
    write(conn, project_id, cube(10.0))
    write(conn, project_id, cube(11.0))
    part_id = db.parts_of(conn, project_id)[0]["id"]
    db.add_revision(conn, part_id, cube(12.0), note="Applied width from the sliders")
    db.add_message(conn, project_id, "user", "make it bigger", {})
    write(conn, project_id, cube(20.0))
    write(conn, project_id, cube(30.0))

    rows = client.get(f"/api/parts/{part_id}/revisions").json()["revisions"]
    assert [r["prompt"] for r in rows] == ["make it bigger", "make it bigger", None, "a cube", "a cube"]
    groups = [r["group"] for r in rows]
    # Rev 4 and 5 answer one message, the slider stands alone, rev 1 and 2 answer the first.
    assert groups[0] == groups[1] == rows[1]["id"]
    assert groups[2] == rows[2]["id"]
    assert groups[3] == groups[4] == rows[4]["id"]
