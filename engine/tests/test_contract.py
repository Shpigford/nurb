"""The served tool list is `tools.json`, byte for byte."""

import base64
import json
import pathlib
import threading
import time

import pytest
from mcp import Client

from nurb import db, mcp_server

TOOLS_FILE = pathlib.Path(mcp_server.TOOLS_FILE)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def conn(tmp_path, monkeypatch):
    # The server answers calls off the event loop, so the connection crosses threads.
    monkeypatch.setenv("NURB_HOME", str(tmp_path / "home"))
    conn = db.connect(tmp_path / "x.db", check_same_thread=False)
    yield conn
    conn.close()


@pytest.mark.anyio
async def test_the_served_tools_are_the_file(conn):
    server = mcp_server.make_server(conn, "http://127.0.0.1:0")
    async with Client(server, raise_exceptions=True) as client:
        result = await client.list_tools()
        # The instructions arrive with initialize, which is the only thing an agent
        # reads before it starts calling tools.
        said = client.instructions

    assert "read_guide" in said and "http://127.0.0.1:0" in said
    served = [
        tool.model_dump(by_alias=True, exclude_none=True, mode="json") for tool in result.tools
    ]
    assert served == json.loads(TOOLS_FILE.read_text(encoding="utf-8"))


CUBE = """from nurb import *


@part
def cube(width=20.0):
    return Box(width, width, width)
"""


@pytest.mark.anyio
async def test_the_renders_of_a_built_part_are_resources(conn):
    server = mcp_server.make_server(conn, "http://127.0.0.1:0")
    async with Client(server, raise_exceptions=True) as client:
        created = await client.call_tool("create_project", {})
        project_id = json.loads(created.content[0].text)["id"]
        await client.call_tool(
            "write_part_source",
            {"project_id": project_id, "part_name": "cube", "source": CUBE},
        )

        listed = await client.list_resources()
        templates = await client.list_resource_templates()
        read = await client.read_resource(f"nurb://render/{project_id}/cube/iso")
        with pytest.raises(Exception):
            await client.read_resource(f"nurb://render/{project_id}/nope/iso")

    uris = [str(resource.uri) for resource in listed.resources]
    assert uris == [f"nurb://render/{project_id}/cube/{view}" for view in ["iso", "back", "top", "under"]]
    assert len(templates.resource_templates) == 1
    assert templates.resource_templates[0].uri_template == "nurb://render/{project_id}/{part}/{view}"
    assert len(read.contents) == 1
    assert base64.b64decode(read.contents[0].blob).startswith(b"\x89PNG")


def test_every_tool_declares_both_hints():
    for tool in mcp_server.TOOLS:
        assert tool.annotations is not None, tool.name
        assert tool.annotations.read_only_hint is not None, tool.name
        assert tool.annotations.destructive_hint is not None, tool.name


def test_tool_names_are_unique():
    names = [tool.name for tool in mcp_server.TOOLS]
    assert len(names) == len(set(names))


@pytest.mark.anyio
async def test_a_call_answers_through_the_server(conn):
    server = mcp_server.make_server(conn, "http://127.0.0.1:0")
    async with Client(server, raise_exceptions=True) as client:
        result = await client.call_tool("create_project", {})
        listed = await client.call_tool("list_projects", {})

    assert result.is_error is False
    assert json.loads(result.content[0].text)["name"]
    assert len(json.loads(listed.content[0].text)["projects"]) == 1


@pytest.mark.anyio
async def test_a_call_waiting_for_the_build_lock_uses_its_arrival_deadline(
    conn, monkeypatch
):
    lock = threading.Lock()
    lock.acquire()
    monkeypatch.setattr(mcp_server, "TOOL_TIMEOUT_SECONDS", 0.02)
    monkeypatch.setattr(mcp_server, "TOOL_SAFETY_SECONDS", 0)
    server = mcp_server.make_server(conn, "http://127.0.0.1:0", lock=lock)

    try:
        started = time.monotonic()
        async with Client(server, raise_exceptions=True) as client:
            result = await client.call_tool(
                "run_build", {"project_id": "project", "part_name": "part"}
            )
        elapsed = time.monotonic() - started
    finally:
        lock.release()

    assert elapsed < 1
    assert result.is_error is True
    assert "deadline" in result.content[0].text


def test_every_tool_in_the_file_has_a_handler_or_a_phase():
    # The file is the runtime source, so the served list cannot drift from it; what
    # can drift is the dispatcher. Every name must be implemented or scheduled.
    names = {tool.name for tool in mcp_server.TOOLS}
    assert names == set(mcp_server.HANDLERS) | set(mcp_server.LATER)
    assert not set(mcp_server.HANDLERS) & set(mcp_server.LATER)


def test_get_project_declares_the_contract_ceiling():
    # get_project carries every part's source at once, so it gets CONTRACT 2's ceiling
    # rather than the 30,000 the build tools live under.
    assert mcp_server.BY_NAME["get_project"].meta["anthropic/maxResultSizeChars"] == 150000


def test_get_project_can_recover_one_large_source_in_bounded_chunks():
    schema = mcp_server.BY_NAME["get_project"].input_schema
    properties = schema["properties"]
    assert "part_name" not in schema["required"]
    assert "pattern" not in properties["part_name"]
    assert properties["source_offset"]["minimum"] == 0
    assert properties["source_limit"]["minimum"] == 1
    assert properties["source_limit"]["maximum"] <= 100000


def test_every_part_name_is_constrained_the_same_way():
    for tool in mcp_server.TOOLS:
        field = tool.input_schema.get("properties", {}).get("part_name")
        if field is not None and tool.name != "get_project":
            assert field["pattern"] == "^[a-z][a-z0-9_]*$", tool.name
