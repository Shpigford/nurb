"""Adversarial size and recovery boundaries for MCP tool results."""

import json

import pytest

from nurb import db, mcp_server

BASE = "http://127.0.0.1:7373"


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    connection = db.connect(tmp_path / "x.db")
    yield connection
    connection.close()


def call(conn, name, args):
    return mcp_server.dispatch(conn, name, args, BASE)


def payload(result):
    assert result.is_error is False, result.content[0].text
    return json.loads(result.content[0].text)


def test_success_and_error_text_are_always_capped(monkeypatch):
    monkeypatch.setattr(mcp_server, "MCP_MAX_CHARS", 300)

    success = mcp_server._ok({"source": "x" * 1000})
    error = mcp_server._error("x" * 1000)

    assert len(success.model_dump_json(by_alias=True, exclude_none=True)) <= 300
    assert "MCP limit" in success.content[0].text
    assert len(error.model_dump_json(by_alias=True, exclude_none=True)) <= 300
    assert "MCP limit" in error.content[0].text


def test_an_oversized_success_remains_json_with_recovery(monkeypatch):
    monkeypatch.setattr(mcp_server, "MCP_MAX_CHARS", 300)

    result = mcp_server._ok(
        {"source": "x" * 1000},
        recovery="read the source in pages",
    )

    body = json.loads(result.content[0].text)
    assert body["truncated"] is True
    assert body["original_characters"] > 1000
    assert body["recovery"] == "read the source in pages"


def test_a_build_deadline_is_a_tool_error(conn, monkeypatch):
    project_id = db.create_project(conn, "slow")

    def timed_out(*args, **kwargs):
        return "run", {
            "glb_bytes": None,
            "render": None,
            "params": [],
            "findings": [],
            "stats": {},
            "inspect": [],
            "error": "build exceeded the deadline",
            "timed_out": True,
        }

    monkeypatch.setattr(mcp_server.engine_run, "run_build", timed_out)
    result = call(
        conn,
        "write_part_source",
        {
            "project_id": project_id,
            "part_name": "cube",
            "source": "from nurb import *\n\n@part\ndef cube():\n    return Box(1, 1, 1)\n",
        },
    )

    assert result.is_error is True
    assert result.content[0].text == "build exceeded the deadline"


def test_dispatch_caps_an_error_that_echoes_untrusted_input(conn):
    result = call(conn, "x" * (mcp_server.MCP_MAX_CHARS * 2), {})
    assert result.is_error is True
    assert (
        len(result.model_dump_json(by_alias=True, exclude_none=True))
        <= mcp_server.MCP_MAX_CHARS
    )
    assert "correct the request and retry" in result.content[0].text


def test_create_project_rejects_an_overlong_escaped_name_without_writing(conn):
    result = call(conn, "create_project", {"name": '"' * 200000})

    assert result.is_error is True
    assert result.content[0].text == "bad arguments for create_project: name: is longer than the maximum 200 characters"
    assert conn.execute("SELECT count(*) FROM projects").fetchone()[0] == 0


def test_large_project_sources_are_omitted_then_recoverable_in_chunks(conn):
    project_id = db.create_project(conn, "large")
    first_source = "# " + '\\\"' * 80000
    second_source = "# " + "x" * 80000
    db.create_part(conn, project_id, "first", first_source)
    db.create_part(conn, project_id, "second", second_source)

    full_result = call(conn, "get_project", {"project_id": project_id})
    full = payload(full_result)
    assert (
        len(full_result.model_dump_json(by_alias=True, exclude_none=True))
        <= mcp_server.PROJECT_MAX_CHARS
    )
    assert full["sources_omitted"] is True
    assert all("source" not in part for part in full["parts"])

    first_result = call(
        conn,
        "get_project",
        {"project_id": project_id, "part_name": "first", "source_limit": 100000},
    )
    first = payload(first_result)["parts"][0]
    assert (
        len(first_result.model_dump_json(by_alias=True, exclude_none=True))
        <= mcp_server.PROJECT_MAX_CHARS
    )
    assert first["source"] == first_source[: first["next_source_offset"]]
    assert first["source_length"] == len(first_source)

    recovered = first["source"]
    page = first
    while "next_source_offset" in page:
        page = payload(
            call(
                conn,
                "get_project",
                {
                    "project_id": project_id,
                    "part_name": "first",
                    "source_offset": page["next_source_offset"],
                    "source_limit": 100000,
                },
            )
        )["parts"][0]
        recovered += page["source"]
    assert recovered == first_source


def test_source_paging_requires_an_exact_part(conn):
    project_id = db.create_project(conn, "large")
    result = call(conn, "get_project", {"project_id": project_id, "source_offset": 1})
    assert result.is_error is True
    assert result.content[0].text == "source_offset and source_limit require part_name"


def test_non_mm_measurements_are_never_labeled_or_overwritten_as_mm(conn):
    project_id = db.create_project(conn, "imported")
    db.set_measurement(conn, project_id, "width", 2, "legacy file", unit="in")
    original_changed_at = db.measurements_of(conn, project_id)[0]["value_changed_at"]

    read = call(conn, "read_measurements", {"project_id": project_id})
    measurement = payload(read)["measurements"][0]
    assert measurement["value"] == 2
    assert measurement["unit"] == "in"
    assert "value_mm" not in measurement
    assert "record_measurement" in measurement["conversion"]

    write = call(
        conn,
        "record_measurement",
        {
            "project_id": project_id,
            "name": "width",
            "value_mm": 50.8,
            "how": "converted with a calculator",
            "provisional": False,
        },
    )
    written = payload(write)
    assert written["measurement"]["value_mm"] == 50.8
    assert written["previous_measurement"] == {"value": 2.0, "unit": "in"}
    row = db.measurements_of(conn, project_id)[0]
    assert (row["value"], row["unit"], row["how"]) == (
        50.8,
        "mm",
        "converted with a calculator",
    )
    assert row["value_changed_at"] != original_changed_at


@pytest.mark.parametrize(
    ("name", "kind"),
    [("_shared", db.PARTS_MODULE_KIND), ("Shared", "module"), ("módulo", "module")],
)
def test_get_project_reads_any_exact_imported_module_name(conn, name, kind):
    project_id = db.create_project(conn, "imported")
    db.create_part(conn, project_id, name, "VALUE = 1", kind=kind)

    part = payload(
        call(conn, "get_project", {"project_id": project_id, "part_name": name})
    )["parts"][0]
    assert (part["name"], part["kind"], part["source"]) == (name, kind, "VALUE = 1")


def test_source_paging_bounds_same_named_root_and_parts_modules(conn):
    project_id = db.create_project(conn, "imported")
    db.create_part(conn, project_id, "_shared", "ROOT", kind="module")
    db.create_part(conn, project_id, "_shared", "PARTS", kind=db.PARTS_MODULE_KIND)

    parts = payload(
        call(
            conn,
            "get_project",
            {"project_id": project_id, "part_name": "_shared", "source_limit": 1},
        )
    )["parts"]

    assert [(part["kind"], part["source"]) for part in parts] == [
        ("module", "R"),
        (db.PARTS_MODULE_KIND, "P"),
    ]
    assert {part["next_source_offset"] for part in parts} == {1}
