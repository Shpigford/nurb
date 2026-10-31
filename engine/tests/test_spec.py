"""The pinned spec: what it refuses, how an amendment merges, what the tools record."""

import copy
import json

import pytest

from nurb import db, mcp_server, spec

BASE = "http://127.0.0.1:7373"

SPEC = {
    "part_name": "bracket",
    "summary": "A shelf bracket that hangs on a slat wall.",
    "params": [
        {"name": "width", "kind": "float", "default": 80.0, "description": "How wide it is."},
        {"name": "ribs", "kind": "int", "default": 3, "description": "How many ribs."},
    ],
    "dimensions": [
        {"name": "slat_width", "value_mm": 25.16, "how": "calipers", "source": "measured", "provisional": False},
        {"name": "wall", "value_mm": 2.0, "how": "four perimeters", "source": "doctrine", "provisional": False},
    ],
    "acceptance": [
        {"criterion": "No wall under the nozzle.", "check": "min_wall"},
        {"criterion": "It stands on the bed.", "check": "stability"},
    ],
    "conventions": {
        "expose_params": True,
        "parameter_style": "plain words the user said",
        "notes": ["The back face mates the wall."],
    },
}


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    conn = db.connect(tmp_path / "x.db")
    yield conn
    conn.close()


def call(conn, name, args):
    return mcp_server.dispatch(conn, name, args, BASE)


def payload(result):
    assert result.is_error is False, result.content[0].text
    return json.loads(result.content[0].text)


def message(result):
    return result.content[0].text


def new_project(conn):
    return payload(call(conn, "create_project", {}))["id"]


def test_a_missing_field_names_the_field():
    broken = copy.deepcopy(SPEC)
    del broken["dimensions"]
    assert any("dimensions" in problem for problem in spec.errors(broken))


def test_a_keyword_part_name_is_refused():
    broken = copy.deepcopy(SPEC)
    broken["part_name"] = "class"
    assert "part_name is a reserved Python keyword" in spec.errors(broken)


def test_a_keyword_parameter_name_is_refused():
    broken = copy.deepcopy(SPEC)
    broken["params"][1]["name"] = "lambda"
    assert "parameter 2 name is a reserved Python keyword" in spec.errors(broken)


def test_the_runtime_only_draft_parameter_is_refused():
    broken = copy.deepcopy(SPEC)
    broken["params"][1]["name"] = "draft"
    assert "parameter 2 name is reserved by the nurb runtime" in spec.errors(broken)


def test_a_duplicated_parameter_name_is_refused():
    broken = copy.deepcopy(SPEC)
    broken["params"][1]["name"] = "width"
    assert 'parameter name "width" is duplicated' in spec.errors(broken)


@pytest.mark.parametrize(
    "kind,default",
    [("float", True), ("float", 1), ("int", 1.5), ("bool", "yes"), ("str", 3)],
)
def test_a_default_that_does_not_match_its_kind_is_refused(kind, default):
    broken = copy.deepcopy(SPEC)
    broken["params"][0]["kind"] = kind
    broken["params"][0]["default"] = default
    assert f'parameter "width" default does not match kind "{kind}"' in spec.errors(broken)


def test_a_good_spec_has_no_errors():
    assert spec.errors(SPEC) == []


def test_merge_replaces_in_place_and_appends():
    merged = spec.merge(
        SPEC,
        {
            "params": [
                {"name": "ribs", "kind": "int", "default": 5, "description": "How many ribs."},
                {"name": "depth", "kind": "float", "default": 40.0, "description": "How deep."},
            ]
        },
    )
    assert [p["name"] for p in merged["params"]] == ["width", "ribs", "depth"]
    assert merged["params"][1]["default"] == 5
    assert merged["dimensions"] == SPEC["dimensions"]
    assert merged["conventions"] == SPEC["conventions"]


def test_merge_keys_acceptance_by_check():
    merged = spec.merge(
        SPEC, {"acceptance": [{"criterion": "Nothing thinner than the nozzle.", "check": "min_wall"}]}
    )
    assert [a["check"] for a in merged["acceptance"]] == ["min_wall", "stability"]
    assert merged["acceptance"][0]["criterion"] == "Nothing thinner than the nozzle."


def test_merge_removes_params_after_replacing_them():
    merged = spec.merge(
        SPEC,
        {
            "params": [{"name": "depth", "kind": "float", "default": 40.0, "description": "How deep."}],
            "remove_params": ["ribs", "depth"],
        },
    )
    assert [p["name"] for p in merged["params"]] == ["width"]


def test_merge_appends_notes():
    merged = spec.merge(SPEC, {"notes": ["Chamfer the bed edges."]})
    assert merged["conventions"]["notes"] == [
        "The back face mates the wall.",
        "Chamfer the bed edges.",
    ]
    assert SPEC["conventions"]["notes"] == ["The back face mates the wall."]


def test_a_pin_missing_a_field_is_refused_and_writes_nothing(conn):
    project_id = new_project(conn)
    args = {"project_id": project_id, **copy.deepcopy(SPEC)}
    del args["acceptance"]
    result = call(conn, "pin_spec", args)
    assert result.is_error is True
    assert "acceptance" in message(result)
    assert conn.execute("SELECT COUNT(*) FROM pinned_specs").fetchone()[0] == 0


def test_a_pin_with_a_keyword_param_is_refused(conn):
    project_id = new_project(conn)
    args = {"project_id": project_id, **copy.deepcopy(SPEC)}
    args["params"][0]["name"] = "width"
    args["params"][1] = {"name": "ribs", "kind": "int", "default": 1.5, "description": "How many."}
    result = call(conn, "pin_spec", args)
    assert message(result).startswith("Spec rejected: ")
    assert conn.execute("SELECT COUNT(*) FROM pinned_specs").fetchone()[0] == 0


def test_an_amend_changes_one_field_and_leaves_the_rest(conn):
    project_id = new_project(conn)
    pinned = payload(call(conn, "pin_spec", {"project_id": project_id, **copy.deepcopy(SPEC)}))
    amended = payload(
        call(
            conn,
            "amend_spec",
            {
                "project_id": project_id,
                "part_name": "bracket",
                "dimensions": [
                    {
                        "name": "slat_width",
                        "value_mm": 25.4,
                        "how": "calipers",
                        "source": "measured",
                        "provisional": False,
                    }
                ],
            },
        )
    )
    assert amended["note"] == "Spec updated."
    assert amended["spec"]["dimensions"][0]["value_mm"] == 25.4
    before = copy.deepcopy(pinned["spec"])
    after = copy.deepcopy(amended["spec"])
    before["dimensions"][0]["value_mm"] = after["dimensions"][0]["value_mm"]
    assert json.dumps(after, sort_keys=True) == json.dumps(before, sort_keys=True)


def test_an_amend_without_a_pinned_spec_is_refused(conn):
    project_id = new_project(conn)
    result = call(conn, "amend_spec", {"project_id": project_id, "part_name": "bracket"})
    assert (
        message(result)
        == 'No pinned spec for "bracket" to amend. pin_spec is for a new part.'
    )


def test_get_project_returns_the_newest_spec_and_the_one_for_a_part(conn):
    project_id = new_project(conn)
    call(conn, "pin_spec", {"project_id": project_id, **copy.deepcopy(SPEC)})
    other = copy.deepcopy(SPEC)
    other["part_name"] = "hook"
    call(conn, "pin_spec", {"project_id": project_id, **other})
    assert payload(call(conn, "get_project", {"project_id": project_id}))["spec"]["part_name"] == "hook"
    call(conn, "write_part_source", {"project_id": project_id, "part_name": "bracket", "source": SOURCE})
    seen = payload(call(conn, "get_project", {"project_id": project_id, "part_name": "bracket"}))
    assert seen["spec"]["part_name"] == "bracket"


def test_a_pin_records_the_spec_in_the_transcript(conn):
    project_id = new_project(conn)
    call(conn, "pin_spec", {"project_id": project_id, "note": "Settled the slat.", **copy.deepcopy(SPEC)})
    row = conn.execute(
        "SELECT content, payload FROM messages WHERE project_id = ? ORDER BY sequence_number DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    recorded = json.loads(row["payload"])
    assert recorded["type"] == "spec_pinned"
    assert recorded["spec"]["part_name"] == "bracket"
    assert recorded["tool"] == "pin_spec"
    assert "note" not in recorded["input"]
    assert row["content"] == "Settled the slat."


SOURCE = """from nurb import *


@part
def bracket(width=80.0):
    return Box(width, width, width)
"""
