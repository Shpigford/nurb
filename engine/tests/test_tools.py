"""What each tool answers, driven through the dispatcher the server runs."""

import base64
import json
import pathlib

import pytest

from nurb import db, folder, mcp_server

NOTCH = pathlib.Path(__file__).parents[1] / "examples" / "notch"
BASE = "http://127.0.0.1:7373"

BROKEN = """from nurb import *


@part
def broken(width=10.0):
    return Box(width, width, 0)
"""

CUBE = """from nurb import *


@part
def cube(width=20.0):
    return Box(width, width, width)
"""

# One wall under the nozzle and one sliver: two findings, so paging has a second page.
ROUGH = """from nurb import *


@part
def rough(width=40.0):
    plate = Box(width, width, 0.3)
    arm = Pos(width / 2, 0, 20) * Box(width, 0.3, 0.3)
    post = Pos(0, 0, 10) * Box(0.4, 0.4, 20)
    return plate + arm + post
"""


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
    assert result.is_error is True
    return result.content[0].text


def new_project(conn):
    return payload(call(conn, "create_project", {}))["id"]


def test_bad_arguments_name_the_field(conn):
    project_id = new_project(conn)
    result = call(conn, "record_measurement", {"project_id": project_id, "name": "rail_width"})
    text = message(result)
    assert text.startswith("bad arguments for record_measurement: ")
    assert "value_mm" in text


def test_get_project_reports_its_top_level_printer_profile(conn):
    project_id = db.create_project(conn, "printer project", 'profile = "prusa_mk4s"\n')

    body = payload(call(conn, "get_project", {"project_id": project_id}))

    assert body["printer"] == "prusa_mk4s"


def test_a_bad_enum_names_its_path(conn):
    project_id = new_project(conn)
    result = call(
        conn,
        "pin_spec",
        {
            "project_id": project_id,
            "part_name": "shelf",
            "summary": "a shelf",
            "params": [{"name": "width", "kind": "foo", "default": 1.0, "description": "wide"}],
            "dimensions": [
                {"name": "w", "value_mm": 1.0, "how": "calipers", "source": "measured", "provisional": False}
            ],
            "acceptance": [{"criterion": "it fits", "check": "min_wall"}],
            "conventions": {"expose_params": True, "parameter_style": "plain words"},
        },
    )
    assert message(result).startswith("bad arguments for pin_spec: params[0].kind: ")


def test_a_part_that_raises_is_a_result_not_a_tool_failure(conn):
    project_id = new_project(conn)
    result = call(
        conn,
        "write_part_source",
        {"project_id": project_id, "part_name": "broken", "source": BROKEN},
    )
    body = payload(result)
    assert body["status"] == "error"
    assert body["passed"] is False
    first = body["error"].splitlines()[:2]
    assert first[0] == "Traceback (most recent call last):"
    assert 'parts/broken.py"' in first[1]


def _png(block):
    assert block.type == "image"
    assert block.mime_type == "image/png"
    data = base64.b64decode(block.data)
    assert data.startswith(b"\x89PNG")
    assert len(block.data) < 80000
    return data


def test_a_passing_build_carries_one_picture_and_a_render_link(conn):
    project_id = new_project(conn)
    result = call(
        conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE}
    )
    body = payload(result)
    assert body["status"] == "ok"
    assert set(body["views"]) == set(mcp_server.raster.VIEWS)
    assert body["look_note"]
    assert len(result.content) == 3
    _png(result.content[1])
    link = result.content[2]
    assert link.type == "resource_link"
    assert link.name == "cube.iso.png"
    assert str(link.uri) == f"nurb://render/{project_id}/cube/iso"
    assert link.mime_type == "image/png"


def test_a_failing_build_has_no_picture(conn):
    project_id = new_project(conn)
    result = call(
        conn,
        "write_part_source",
        {"project_id": project_id, "part_name": "broken", "source": BROKEN},
    )
    assert payload(result)["status"] == "error"
    assert len(result.content) == 1


def test_a_build_stores_its_render(conn):
    project_id = new_project(conn)
    call(conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE})
    row = conn.execute("SELECT render FROM build_runs").fetchone()
    assert row["render"].startswith(b"\x89PNG")


def test_look_without_a_passing_build_says_to_build(conn):
    project_id = new_project(conn)
    call(
        conn,
        "write_part_source",
        {"project_id": project_id, "part_name": "broken", "source": BROKEN},
    )
    result = call(conn, "look", {"project_id": project_id, "part_name": "broken"})
    assert message(result) == "broken has no successful build yet; call run_build first"


def test_look_shows_the_last_build_that_worked_and_says_when_it_is_stale(conn):
    project_id = new_project(conn)
    call(conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE})
    result = call(conn, "look", {"project_id": project_id, "part_name": "cube"})
    body = payload(result)
    assert body["part_name"] == "cube"
    assert body["stale"] is False
    assert len(result.content) == 3
    _png(result.content[1])
    assert str(result.content[2].uri) == f"nurb://render/{project_id}/cube/iso"

    broken = CUBE.replace("return Box(width, width, width)", "return Box(width, width, 0)", 1)
    assert payload(
        call(
            conn,
            "write_part_source",
            {"project_id": project_id, "part_name": "cube", "source": broken},
        )
    )["status"] == "error"
    after = payload(call(conn, "look", {"project_id": project_id, "part_name": "cube"}))
    assert after["stale"] is True


def test_look_is_stale_when_a_transitively_used_measurement_changes(conn):
    project_id = db.create_project(conn, "measured")
    db.set_measurement(conn, project_id, "gap", 10, "calipers")
    db.create_part(
        conn,
        project_id,
        "_measurements",
        'from nurb import measured\n\nGAP = measured("gap")\n',
        kind=db.PARTS_MODULE_KIND,
    )
    db.create_part(
        conn,
        project_id,
        "_shared",
        "from ._measurements import GAP\n",
        kind=db.PARTS_MODULE_KIND,
    )
    db.create_part(
        conn,
        project_id,
        "shelf",
        "from nurb import *\nfrom parts._shared import GAP\n\n@part\ndef shelf():\n    return Box(GAP, 10, 10)\n",
    )
    assert payload(call(conn, "run_build", {"project_id": project_id, "part_name": "shelf"}))[
        "status"
    ] == "ok"
    assert payload(call(conn, "look", {"project_id": project_id, "part_name": "shelf"}))[
        "stale"
    ] is False

    payload(
        call(
            conn,
            "record_measurement",
            {
                "project_id": project_id,
                "name": "gap",
                "value_mm": 12,
                "how": "calipers, twice",
                "provisional": False,
            },
        )
    )

    assert payload(call(conn, "look", {"project_id": project_id, "part_name": "shelf"}))[
        "stale"
    ] is True


def test_look_backfills_a_missing_render(conn):
    project_id = new_project(conn)
    call(conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE})
    with conn:
        conn.execute("UPDATE build_runs SET render = NULL")
    result = call(conn, "look", {"project_id": project_id, "part_name": "cube"})
    assert result.is_error is False
    assert conn.execute("SELECT render FROM build_runs").fetchone()["render"] is not None


def test_writing_the_same_source_twice_does_not_rebuild(conn):
    project_id = new_project(conn)
    args = {"project_id": project_id, "part_name": "cube", "source": CUBE}
    call(conn, "write_part_source", args)
    assert payload(call(conn, "write_part_source", args)) == {
        "changed": False,
        "note": "source unchanged from the current revision",
    }


def test_writing_the_same_source_records_the_tool_step_without_a_revision(conn):
    project_id = new_project(conn)
    args = {"project_id": project_id, "part_name": "cube", "source": CUBE}
    call(conn, "write_part_source", args)
    revisions = conn.execute("SELECT count(*) FROM part_revisions").fetchone()[0]
    builds = conn.execute("SELECT count(*) FROM build_runs").fetchone()[0]

    call(conn, "write_part_source", {**args, "note": "confirmed current source"})

    assert conn.execute("SELECT count(*) FROM part_revisions").fetchone()[0] == revisions
    assert conn.execute("SELECT count(*) FROM build_runs").fetchone()[0] == builds
    row = conn.execute("SELECT * FROM messages ORDER BY sequence_number DESC LIMIT 1").fetchone()
    assert row["content"] == "confirmed current source"
    assert json.loads(row["payload"]) == {
        "tool": "write_part_source",
        "summary": "cube unchanged",
        "part_name": "cube",
    }


def test_an_edit_changes_the_source_and_builds(conn):
    project_id = new_project(conn)
    call(
        conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE}
    )
    result = call(
        conn,
        "edit_part_source",
        {
            "project_id": project_id,
            "part_name": "cube",
            "old_string": "width=20.0",
            "new_string": "width=30.0",
        },
    )
    assert payload(result)["status"] == "ok"
    part = mcp_server._part(conn, project_id, "cube")
    assert "width=30.0" in part["source"]


def test_an_ambiguous_edit_is_refused(conn):
    project_id = new_project(conn)
    call(
        conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE}
    )
    result = call(
        conn,
        "edit_part_source",
        {
            "project_id": project_id,
            "part_name": "cube",
            "old_string": "width",
            "new_string": "w",
        },
    )
    assert message(result).startswith("old_string matches ")


def test_an_edit_without_a_source_says_what_to_call(conn):
    project_id = new_project(conn)
    result = call(
        conn,
        "edit_part_source",
        {"project_id": project_id, "part_name": "cube", "old_string": "a", "new_string": "b"},
    )
    assert message(result) == "no source yet for cube; call write_part_source first"


def test_building_an_unknown_part_is_refused(conn):
    project_id = new_project(conn)
    result = call(conn, "run_build", {"project_id": project_id, "part_name": "nothing"})
    assert message(result) == (
        "no part called nothing in this project; call write_part_source first"
    )


def test_a_changed_measurement_makes_a_built_part_stale(conn):
    project_id, _ = folder.import_folder(conn, NOTCH)
    call(conn, "run_build", {"project_id": project_id, "part_name": "mount_akrobin_rail"})

    args = {
        "project_id": project_id,
        "name": "akrobin_leg_thickness",
        "value_mm": 3.1,
        "how": "calipers, twice",
        "provisional": False,
    }
    first = payload(call(conn, "record_measurement", args))
    assert first["measurement"]["value_mm"] == 3.1
    assert first["previous_value_mm"] == 2.75
    assert "mount_akrobin_rail" in first["stale_parts"]

    again = payload(call(conn, "record_measurement", args))
    assert again["previous_value_mm"] == 3.1
    assert again["stale_parts"] == []


def test_a_measurement_used_through_a_shared_module_makes_the_part_stale(conn):
    project_id, _ = folder.import_folder(conn, NOTCH)
    call(conn, "run_build", {"project_id": project_id, "part_name": "shelf_basic"})

    body = payload(
        call(
            conn,
            "record_measurement",
            {
                "project_id": project_id,
                "name": "bracket_pitch",
                "value_mm": 25.2,
                "how": "calipers, twice",
                "provisional": False,
            },
        )
    )
    assert "shelf_basic" in body["stale_parts"]


def test_an_imported_spaced_measurement_updates_exactly_through_a_parts_module(conn):
    project_id = db.create_project(conn, "imported")
    db.set_measurement(conn, project_id, "shelf depth", 10, "legacy file")
    db.create_part(
        conn,
        project_id,
        "_shared",
        'from nurb import measured\n\nDEPTH = measured (\n    name="shelf depth",\n)\n',
        kind=db.PARTS_MODULE_KIND,
    )
    source = """from nurb import *

from parts._shared import DEPTH


@part
def shelf():
    return Box(DEPTH, 10, 10)
"""
    db.create_part(conn, project_id, "shelf", source)
    assert payload(call(conn, "run_build", {"project_id": project_id, "part_name": "shelf"}))[
        "status"
    ] == "ok"

    body = payload(
        call(
            conn,
            "record_measurement",
            {
                "project_id": project_id,
                "name": "shelf depth",
                "value_mm": 12,
                "how": "calipers",
                "provisional": False,
            },
        )
    )
    assert body["measurement"]["name"] == "shelf depth"
    assert body["previous_value_mm"] == 10
    assert body["stale_parts"] == ["shelf"]
    assert [row["name"] for row in db.measurements_of(conn, project_id)] == ["shelf depth"]
    uses = payload(call(conn, "read_measurements", {"project_id": project_id}))["parts"]
    assert uses == [{"name": "shelf", "uses": ["shelf depth"]}]


def test_measurement_dependency_follows_relative_parts_module_imports(conn):
    project_id = db.create_project(conn, "imported")
    db.set_measurement(conn, project_id, "gap", 10, "legacy file")
    db.create_part(
        conn,
        project_id,
        "_measurements",
        'from nurb import measured\n\nGAP = measured("gap")\n',
        kind=db.PARTS_MODULE_KIND,
    )
    db.create_part(
        conn,
        project_id,
        "_shared",
        "from ._measurements import GAP\n",
        kind=db.PARTS_MODULE_KIND,
    )
    db.create_part(
        conn,
        project_id,
        "shelf",
        "from nurb import *\nfrom parts._shared import GAP\n\n@part\ndef shelf():\n    return Box(GAP, 10, 10)\n",
    )
    assert payload(call(conn, "run_build", {"project_id": project_id, "part_name": "shelf"}))[
        "status"
    ] == "ok"

    body = payload(
        call(
            conn,
            "record_measurement",
            {
                "project_id": project_id,
                "name": "gap",
                "value_mm": 12,
                "how": "calipers",
                "provisional": False,
            },
        )
    )
    assert body["stale_parts"] == ["shelf"]


def test_measurement_dependency_follows_nested_project_file_modules(conn):
    project_id = db.create_project(conn, "imported")
    db.set_measurement(conn, project_id, "gap", 10, "calipers")
    db.add_project_file(conn, project_id, "helpers/__init__.py", b"from .sizes import GAP\n")
    db.add_project_file(
        conn,
        project_id,
        "helpers/sizes.py",
        b'from nurb import measured\n\nGAP = measured("gap")\n',
    )
    db.create_part(
        conn,
        project_id,
        "shelf",
        "from nurb import *\nfrom helpers import GAP\n\n@part\ndef shelf():\n    return Box(GAP, 10, 10)\n",
    )
    assert payload(call(conn, "run_build", {"project_id": project_id, "part_name": "shelf"}))[
        "status"
    ] == "ok"

    body = payload(
        call(
            conn,
            "record_measurement",
            {
                "project_id": project_id,
                "name": "gap",
                "value_mm": 12,
                "how": "calipers, twice",
                "provisional": False,
            },
        )
    )
    assert body["stale_parts"] == ["shelf"]
    assert payload(call(conn, "read_measurements", {"project_id": project_id}))["parts"] == [
        {"name": "shelf", "uses": ["gap"]}
    ]


def test_measurement_dependencies_distinguish_same_named_root_and_parts_modules(conn):
    project_id = db.create_project(conn, "imported")
    db.set_measurement(conn, project_id, "root_width", 2, "calipers")
    db.set_measurement(conn, project_id, "parts_width", 12, "calipers")
    db.create_part(
        conn,
        project_id,
        "_shared",
        'from nurb import measured\n\nROOT_WIDTH = measured("root_width")\n',
        kind="module",
    )
    db.create_part(
        conn,
        project_id,
        "_shared",
        'from nurb import measured\n\nPARTS_WIDTH = measured("parts_width")\n',
        kind=db.PARTS_MODULE_KIND,
    )
    db.create_part(
        conn,
        project_id,
        "shelf",
        "from nurb import *\nfrom _shared import ROOT_WIDTH\nfrom parts._shared import PARTS_WIDTH\n\n@part\ndef shelf():\n    return Box(ROOT_WIDTH + PARTS_WIDTH, 10, 10)\n",
    )
    assert payload(call(conn, "run_build", {"project_id": project_id, "part_name": "shelf"}))[
        "status"
    ] == "ok"

    uses = payload(call(conn, "read_measurements", {"project_id": project_id}))["parts"]
    assert uses == [{"name": "shelf", "uses": ["root_width", "parts_width"]}]
    for name in ("root_width", "parts_width"):
        body = payload(
            call(
                conn,
                "record_measurement",
                {
                    "project_id": project_id,
                    "name": name,
                    "value_mm": 20,
                    "how": "calipers, twice",
                    "provisional": False,
                },
            )
        )
        assert body["stale_parts"] == ["shelf"]


def test_a_new_measurement_has_no_previous_value(conn):
    project_id = new_project(conn)
    body = payload(
        call(
            conn,
            "record_measurement",
            {
                "project_id": project_id,
                "name": "Shelf Depth",
                "value_mm": 120.0,
                "how": "user stated",
                "provisional": True,
            },
        )
    )
    assert "previous_value_mm" not in body
    # Case survives: a part reads the name it was given, exactly.
    assert body["measurement"]["name"] == "Shelf_Depth"
    assert body["stale_parts"] == []


def test_measurements_report_which_parts_read_them(conn):
    project_id, _ = folder.import_folder(conn, NOTCH)
    body = payload(call(conn, "read_measurements", {"project_id": project_id}))
    uses = {row["name"]: row["uses"] for row in body["parts"]}
    assert "akrobin_leg_thickness" in uses["mount_akrobin_rail"]
    assert "bracket_pitch" in uses["shelf_basic"]
    assert "system" not in uses


def test_a_non_finite_measurement_is_refused(conn):
    project_id = new_project(conn)
    result = call(
        conn,
        "record_measurement",
        {
            "project_id": project_id,
            "name": "gap",
            "value_mm": float("inf"),
            "how": "calipers",
            "provisional": False,
        },
    )
    assert message(result) == "value_mm must be a finite number"


def test_a_blank_how_is_refused(conn):
    project_id = new_project(conn)
    result = call(
        conn,
        "record_measurement",
        {
            "project_id": project_id,
            "name": "gap",
            "value_mm": 3.0,
            "how": "   ",
            "provisional": False,
        },
    )
    assert message(result) == "how is required: say where the number came from"


def test_a_name_held_by_a_module_is_refused(conn):
    project_id, _ = folder.import_folder(conn, NOTCH)
    result = call(
        conn, "write_part_source", {"project_id": project_id, "part_name": "system", "source": CUBE}
    )
    assert message(result) == "system is a module in this project; pick another name"


def test_a_placeholder_name_is_neither_empty_nor_untitled(conn):
    first = payload(call(conn, "create_project", {}))
    second = payload(call(conn, "create_project", {}))
    assert first["name"] and first["name"] != "Untitled"
    assert first["name"] != second["name"]


def test_a_project_reads_back_with_its_parts(conn):
    project_id, _ = folder.import_folder(conn, NOTCH)
    body = payload(call(conn, "get_project", {"project_id": project_id}))
    parts = {row["name"]: row for row in body["parts"]}
    assert parts["shelf_basic"]["last_build"] is None
    assert "from nurb import *" in parts["shelf_basic"]["source"]
    assert body["spec"] is None

    call(conn, "run_build", {"project_id": project_id, "part_name": "shelf_basic"})
    again = payload(call(conn, "get_project", {"project_id": project_id}))
    built = {row["name"]: row for row in again["parts"]}["shelf_basic"]["last_build"]
    assert built["status"] == "ok"


def test_an_unknown_project_says_to_list_them(conn):
    result = call(conn, "get_project", {"project_id": "nope"})
    assert message(result) == "no project nope; call list_projects"


def test_projects_list_with_their_counts(conn):
    project_id, _ = folder.import_folder(conn, NOTCH)
    rows = payload(call(conn, "list_projects", {}))["projects"]
    assert len(rows) == 1
    assert rows[0]["id"] == project_id
    assert rows[0]["parts"] == 13
    assert rows[0]["last_built_at"] is None


def test_findings_page_and_then_run_out(conn):
    project_id = new_project(conn)
    call(
        conn, "write_part_source", {"project_id": project_id, "part_name": "rough", "source": ROUGH}
    )
    first = payload(
        call(conn, "read_findings", {"project_id": project_id, "part_name": "rough", "limit": 1})
    )
    assert first["total_findings"] == 2
    assert len(first["findings"]) == 1
    assert "face" not in first["findings"][0]
    assert first["next_offset"] == 1
    assert first["inspect"]

    second = payload(
        call(
            conn,
            "read_findings",
            {"project_id": project_id, "part_name": "rough", "offset": 1, "limit": 1},
        )
    )
    assert "next_offset" not in second
    assert "inspect" not in second


def test_findings_before_any_build_are_a_note(conn):
    project_id, _ = folder.import_folder(conn, NOTCH)
    body = payload(
        call(conn, "read_findings", {"project_id": project_id, "part_name": "shelf_basic"})
    )
    assert body == {"note": "no builds yet; call run_build first"}


def test_a_revision_that_never_built_reports_no_build(conn):
    # add_revision commits before the build runs, so a build that raises leaves the
    # part holding new source and the old revision holding the last passing run.
    project_id = new_project(conn)
    call(
        conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE}
    )
    part = mcp_server._part(conn, project_id, "cube")
    db.add_revision(conn, part["id"], CUBE.replace("20.0", "25.0"))

    body = payload(call(conn, "get_project", {"project_id": project_id}))
    assert {row["name"]: row for row in body["parts"]}["cube"]["last_build"] is None
    assert payload(
        call(conn, "read_findings", {"project_id": project_id, "part_name": "cube"})
    ) == {"note": "no builds yet; call run_build first"}


@pytest.mark.parametrize("filler", ["x", '"', "😀"])
def test_a_huge_build_error_keeps_its_head_and_tail_in_both_readers(conn, filler):
    project_id = new_project(conn)
    source = f'''from nurb import *


@part
def broken():
    raise RuntimeError("ERROR_HEAD:" + {filler!r} * 40000 + ":ERROR_TAIL")
'''
    built = call(
        conn,
        "write_part_source",
        {"project_id": project_id, "part_name": "broken", "source": source},
    )
    built_body = payload(built)
    assert len(built.content[0].text) <= mcp_server.RESULT_MAX_CHARS
    assert built_body["status"] == "error"
    assert "ERROR_HEAD" in built_body["error"]
    assert "ERROR_TAIL" in built_body["error"]
    assert "use read_findings for the stored build error" in built_body["error"]

    part = mcp_server._part(conn, project_id, "broken")
    run = db.latest_run(conn, part["id"], part["current_revision_id"])
    assert len(run["error"]) > mcp_server.RESULT_MAX_CHARS
    assert "ERROR_HEAD" in run["error"]
    assert "ERROR_TAIL" in run["error"]

    found = call(conn, "read_findings", {"project_id": project_id, "part_name": "broken"})
    found_body = payload(found)
    assert len(found.content[0].text) <= mcp_server.RESULT_MAX_CHARS
    assert found_body["status"] == "error"
    assert "ERROR_HEAD" in found_body["error"]
    assert "ERROR_TAIL" in found_body["error"]
    assert "middle of stored build error omitted" in found_body["error"]
    assert "truncated" not in found_body


def test_an_unknown_tool_is_refused(conn):
    assert message(call(conn, "nope", {})) == "unknown tool nope"


def test_every_write_appends_a_numbered_message(conn):
    project_id = new_project(conn)
    call(
        conn,
        "write_part_source",
        {"project_id": project_id, "part_name": "cube", "source": CUBE, "note": "first pass"},
    )
    call(conn, "run_build", {"project_id": project_id, "part_name": "cube"})

    rows = conn.execute(
        "SELECT * FROM messages WHERE project_id = ? ORDER BY sequence_number", (project_id,)
    ).fetchall()
    assert [row["sequence_number"] for row in rows] == [1, 2, 3]
    assert [json.loads(row["payload"])["tool"] for row in rows] == [
        "create_project",
        "write_part_source",
        "run_build",
    ]
    assert rows[0]["role"] == "assistant"
    assert rows[1]["content"] == "first pass"
    assert json.loads(rows[2]["payload"])["summary"] == "cube built: ok, 0 findings"


def rows_of(conn, project_id):
    return conn.execute(
        "SELECT * FROM messages WHERE project_id = ? ORDER BY sequence_number", (project_id,)
    ).fetchall()


def test_a_read_tool_leaves_one_step_in_the_transcript(conn):
    from nurb import serve

    project_id = new_project(conn)
    payload(call(conn, "get_project", {"project_id": project_id}))

    rows = rows_of(conn, project_id)
    assert [row["role"] for row in rows] == ["assistant", "event"]
    shaped = serve._message(conn, rows[1])
    assert shaped["payload"]["type"] == "step"
    assert shaped["payload"]["step"]["status"] == "done"
    assert shaped["payload"]["step"]["elapsed_s"] >= 0


def test_a_write_tool_leaves_one_line_not_two(conn):
    project_id = new_project(conn)
    call(
        conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE}
    )

    rows = rows_of(conn, project_id)
    assert [json.loads(row["payload"])["tool"] for row in rows] == [
        "create_project",
        "write_part_source",
    ]
    assert rows[1]["role"] == "assistant"


def test_a_refused_tool_call_leaves_a_failed_step(conn):
    from nurb import serve

    project_id = new_project(conn)
    message(call(conn, "run_build", {"project_id": project_id, "part_name": "nothing"}))

    rows = rows_of(conn, project_id)
    assert len(rows) == 2
    step = serve._message(conn, rows[1])["payload"]["step"]
    assert step["status"] == "failed"
    assert step["verb"] == "run"


SHELF = """from nurb import *
from system import WALL


@part
def {name}(width=20.0):
    return Box(width, width, WALL)
"""


def test_a_shared_file_change_builds_one_importer_now_and_queues_the_rest(conn):
    """One edit to the family's shared file moves every part that imports it."""
    from nurb import engine_run

    project_id = new_project(conn)
    first = payload(call(conn, "write_shared_source", {"project_id": project_id, "name": "system", "source": "WALL = 2.0\n"}))
    assert first["importers"] == [] and "no part imports system" in first["note"]
    for name in ("bin_a", "bin_b"):
        payload(call(conn, "write_part_source", {"project_id": project_id, "part_name": name, "source": SHELF.format(name=name)}))
    while engine_run.take_rebuild():
        pass

    result = payload(
        call(conn, "edit_shared_source", {"project_id": project_id, "name": "system", "old_string": "WALL = 2.0", "new_string": "WALL = 3.0"})
    )
    assert result["importers"] == ["bin_a", "bin_b"]
    assert result["status"] == "ok"
    assert result["stats"]["bbox"][2] == pytest.approx(3.0)
    queued = engine_run.take_rebuild()
    assert queued is not None and engine_run.take_rebuild() is None
    names = {row["id"]: row["name"] for row in db.parts_of(conn, project_id)}
    assert names[queued] == "bin_b"


def test_a_shared_file_refuses_bad_source_and_a_parts_name(conn):
    project_id = new_project(conn)
    payload(call(conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE}))
    assert "does not parse: line 1" in message(
        call(conn, "write_shared_source", {"project_id": project_id, "name": "system", "source": "WALL = (\n"})
    )
    assert "is a part in this project" in message(
        call(conn, "write_shared_source", {"project_id": project_id, "name": "cube", "source": "WALL = 2.0\n"})
    )


TWIN = """from nurb import *


@part
def {name}(width=20.0, height=8.0):
    plate = Box(width, width, 2.0)
    rib = Pos(0, 0, height / 2) * Box(width, 2.0, height)
    body = plate + rib
    return body
"""


def test_a_build_names_what_it_repeats_from_a_sibling(conn):
    """The moment a system is waiting to be lifted, the build that creates it says so."""
    project_id = new_project(conn)
    first = payload(call(conn, "write_part_source", {"project_id": project_id, "part_name": "bin_a", "source": TWIN.format(name="bin_a")}))
    assert "repeats" not in first
    second = payload(call(conn, "write_part_source", {"project_id": project_id, "part_name": "bin_b", "source": TWIN.format(name="bin_b")}))
    [repeat] = second["repeats"]
    assert repeat["with"] == ["bin_a"] and repeat["statements"] >= 3
    assert "Box(width, 2.0, height)" in repeat["source"]
    assert "write_shared_source" in second["repeats_note"]


def test_get_project_leads_with_the_system_it_should_build_on(conn):
    project_id = new_project(conn)
    assert payload(call(conn, "get_project", {"project_id": project_id}))["system"] is None
    payload(call(conn, "write_shared_source", {"project_id": project_id, "name": "system", "source": "WALL = 2.0  # every wall\n\ndef slab(w):\n    return w\n"}))
    project = payload(call(conn, "get_project", {"project_id": project_id}))
    assert list(project)[2] == "system"
    [file] = project["system"]["shared_files"]
    assert file == {"name": "system", "settings": ["WALL"], "pieces": ["slab"], "used_by": 0}
    assert "Build new parts on its shared files" in project["system"]["note"]


def test_a_tool_saying_a_part_s_old_name_is_told_the_new_one(conn):
    project_id = db.create_project(conn, "shelf")
    payload(call(conn, "write_part_source", {"project_id": project_id, "part_name": "cube", "source": CUBE}))
    part = next(row for row in db.parts_of(conn, project_id) if row["name"] == "cube")
    db.rename_part(conn, part["id"], "block")

    # An agent mid-turn still says the old name. A save must not make a second part.
    stale = {"project_id": project_id, "part_name": "cube", "source": CUBE}
    refused = call(conn, "write_part_source", stale)
    assert refused.is_error and "renamed to block" in refused.content[0].text
    assert [row["name"] for row in db.parts_of(conn, project_id)] == ["block"]

    # Once no running turn could mean the old part, the name is free again.
    conn.execute("UPDATE part_revisions SET created_at = '2020-01-01T00:00:00+00:00'")
    payload(call(conn, "write_part_source", stale))
    assert sorted(row["name"] for row in db.parts_of(conn, project_id)) == ["block", "cube"]
