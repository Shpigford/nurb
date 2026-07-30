"""Parameters from the signature to the viewer and back.

The keyword defaults are the parameters, so everything here is derived from a part's
signature. Nothing in these tests declares a range, a type or a list of names, because
nothing in nurb does either.
"""

import asyncio
import contextlib
import json
import pathlib

import pytest

from nurb import builder
from nurb.server import Server

PART = '''from nurb import *


@part
def thing(count=4, height=42.0, label="x", draft=False):
    return Box(count, height, 5)
'''


@pytest.fixture
def project(tmp_path):
    (tmp_path / "parts").mkdir()
    (tmp_path / "parts" / "thing.py").write_text(PART)
    return tmp_path


@pytest.fixture
def part_file(project):
    return project / "parts" / "thing.py"


def params(path, **overrides):
    rows = builder.build(path, overrides=overrides or None)[1]
    return {r["name"]: r for r in rows}


def test_every_keyword_default_becomes_a_parameter_in_signature_order(part_file):
    rows = builder.build(part_file)[1]
    assert [r["name"] for r in rows] == ["count", "height", "label"]


def test_draft_is_the_runtime_s_and_never_a_control(part_file):
    """It is injected by the runtime, not passed by a caller, so it is not a knob."""
    assert "draft" not in params(part_file)


def test_the_kind_is_what_the_default_was_written_as(part_file):
    """JavaScript has one number type, so 1.0 arrives as 1. Only this can tell them
    apart, and it decides whether a slider steps by one or continuously."""
    got = params(part_file)
    assert got["count"]["kind"] == "int"
    assert got["height"]["kind"] == "float"
    assert got["label"]["kind"] == "other"


def test_the_kind_follows_the_default_not_wherever_the_slider_is(part_file):
    """A float parameter dragged onto a whole number is still a float parameter.

    JSON carries 2.0 as 2, so reading the kind off the current value reported `int`,
    and the panel came back after a reload with an integer slider on a chamfer.
    """
    got = params(part_file, height=2)
    assert got["height"] == {"name": "height", "default": 42.0, "value": 2, "kind": "float",
                             "doc": None}


def test_an_override_moves_the_value_and_leaves_the_default_alone(part_file):
    got = params(part_file, count=9)
    assert got["count"] == {"name": "count", "default": 4, "value": 9, "kind": "int",
                            "doc": None}
    assert got["height"]["value"] == got["height"]["default"] == 42.0


def test_an_override_naming_nothing_says_which_name(part_file):
    with pytest.raises(builder.UnknownParams) as exc:
        builder.build(part_file, overrides={"nope": 1, "alsono": 2})
    assert exc.value.names == ["alsono", "nope"]
    assert isinstance(exc.value, builder.BuildError)   # still catchable as a build failure


def test_a_default_json_cannot_carry_does_not_take_the_message_down(tmp_path):
    """A part may default to any object, and the payload is one websocket message: an
    unencodable default has to cost its own row, not every part's geometry."""
    (tmp_path / "parts").mkdir()
    path = tmp_path / "parts" / "odd.py"
    path.write_text("from nurb import *\n\n\n@part\ndef odd(where=Vector(1, 2, 3)):\n    return Box(1, 1, 1)\n")
    rows = builder.build(path)[1]
    assert rows[0]["kind"] == "other"
    assert json.dumps(rows)     # the point of the test


DOCUMENTED = '''from nurb import *


@part
def told(count=4, height=42.0, draft=False):
    """A test part that explains its parameters.

    count: how many notches it gets
    height: overall height, base to
        the top of the tallest notch
    draft: injected by the runtime, never a knob
    Note: this line names no parameter and belongs to nothing
    """
    return Box(count, height, 5)
'''


def test_a_docstring_line_naming_a_parameter_becomes_its_doc(tmp_path):
    """The tooltip on a slider comes from the part's own docstring, the one place a
    function explains itself, so there is no parallel declaration to drift. A
    deeper-indented line continues the one above it; `draft` and prose lines whose
    first word is no parameter belong to nobody."""
    (tmp_path / "parts").mkdir()
    path = tmp_path / "parts" / "told.py"
    path.write_text(DOCUMENTED)
    got = params(path)
    assert got["count"]["doc"] == "how many notches it gets"
    assert got["height"]["doc"] == "overall height, base to the top of the tallest notch"
    assert "draft" not in got
    assert "Note" not in got


def test_a_part_with_no_docstring_reports_no_docs(part_file):
    assert all(r["doc"] is None for r in params(part_file).values())


# ---- the server side ----


def run(server, message):
    async def go():
        server.queue = asyncio.Queue()
        await server.command(json.dumps(message))
        return [server.queue.get_nowait() for _ in range(server.queue.qsize())]

    return asyncio.run(go())


def test_params_are_held_per_part_and_ask_for_a_rebuild(project, part_file):
    server = Server(project)
    queued = run(server, {"type": "params", "name": "thing", "values": {"count": 7}})
    assert server.overrides == {"thing": {"count": 7}}
    assert queued == [str(part_file)]


def test_sending_nothing_back_is_how_a_part_returns_to_its_file(project):
    server = Server(project)
    run(server, {"type": "params", "name": "thing", "values": {"count": 7}})
    run(server, {"type": "params", "name": "thing", "values": {}})
    assert server.overrides == {}


def test_the_polish_toggle_flips_draft_and_rebuilds_the_project(project, part_file):
    """The viewer shows the polished part by default; the toggle is the escape hatch,
    and flipping it rebuilds everything so no part is left in the old mode."""
    server = Server(project)
    assert server.draft is False
    queued = run(server, {"type": "draft", "on": True})
    assert server.draft is True
    assert queued == [str(part_file)]
    run(server, {"type": "draft", "on": False})
    assert server.draft is False


def test_a_message_naming_no_part_is_ignored(project):
    server = Server(project)
    for bad in [{"type": "params", "name": "../secrets", "values": {"count": 1}},
                {"type": "params", "name": None, "values": {"count": 1}},
                {"type": "apply", "name": "nothing_here"}]:
        assert run(server, bad) == []
    assert server.overrides == {}


def test_a_name_cannot_reach_a_file_outside_parts(project):
    """A command names a part, never a path. `../victim` reached a real file and
    `apply` rewrote it."""
    victim = project / "victim.py"
    original = "from nurb import *\n\n\n@part\ndef victim(count=1):\n    return Box(1, 1, 1)\n"
    victim.write_text(original)
    server = Server(project)
    for escape in ["../victim", "../../victim", "./../victim", "sub/../../victim"]:
        server.overrides[escape] = {"count": 99}
        assert run(server, {"type": "apply", "name": escape}) == []
    assert victim.read_text() == original


def test_a_server_with_no_rebuild_loop_refuses_to_write(project, part_file):
    """`nurb render` stands up a Server with no watcher and no queue purely to serve a
    screenshot. It used to crash on a slider and write the part file on an apply."""
    original = part_file.read_text()
    render_server = Server(project)          # exactly what render.py builds: queue is None
    assert render_server.queue is None
    for msg in [{"type": "params", "name": "thing", "values": {"count": 7}},
                {"type": "apply", "name": "thing"}]:
        asyncio.run(render_server.command(json.dumps(msg)))   # must not raise
    assert render_server.overrides == {}
    assert part_file.read_text() == original


def test_apply_writes_the_defaults_and_stops_overriding_them(project, part_file):
    server = Server(project)
    run(server, {"type": "params", "name": "thing", "values": {"count": 7}})
    run(server, {"type": "apply", "name": "thing"})
    assert "count=7" in part_file.read_text()
    assert server.overrides == {}     # the file says it now, so it is not an override


def test_an_override_left_on_a_parameter_an_edit_removed_is_dropped(project, part_file):
    """The file is the authority. Reporting this as a broken part would name a
    parameter the user never typed."""
    server = Server(project)
    server.overrides["thing"] = {"count": 7, "gone": 1}
    entry = server.rebuild(part_file)
    assert entry["error"] is None
    assert server.overrides["thing"] == {"count": 7}
    assert {r["name"]: r["value"] for r in entry["params"]}["count"] == 7


def test_the_payload_the_browser_receives_carries_the_parameters(project, part_file):
    server = Server(project)
    entry = server.rebuild(part_file)
    meta = json.loads(json.dumps(server._wire(entry)))
    assert [r["name"] for r in meta["params"]] == ["count", "height", "label"]
    assert "shape" not in meta and "glb" not in meta


def test_one_part_has_no_family_to_share_anything_with(project, part_file):
    """A constant is only a family constant once there is a family. Two parts agreeing
    is a coincidence; the panel should not start folding things away on the strength of
    it, and a project with one part has nothing to compare against at all."""
    server = Server(project)
    server.rebuild(part_file)
    meta = server._wire(server.state[part_file.stem])
    assert all(not r["family"] for r in meta["params"])


def test_what_most_parts_declare_identically_is_a_family_constant(project, part_file):
    """Name and default both have to match, which is what keeps a per-part count out."""
    source = part_file.read_text()
    for name, count in (("second", 9), ("third", 10), ("fourth", 11)):
        (part_file.parent / f"{name}.py").write_text(
            source.replace("thing(", f"{name}(").replace("count=4", f"count={count}")
        )
    server = Server(project)
    for path in sorted(part_file.parent.glob("*.py")):
        server.rebuild(path)
    family = {
        r["name"]
        for r in server._wire(server.state["second"])["params"]
        if r["family"]
    }
    assert "height" in family  # same default in all four
    assert "count" not in family  # 2 in one part and 9 in three


def test_a_deleted_part_is_forgotten_rather_than_left_in_the_list(project, part_file):
    """Through the drain, which is what the watcher actually calls.

    A part that is gone from disk but still listed is one you can select, drag sliders
    on and export, none of which exist. It used to sit there until the server restarted.
    """
    server = Server(project)
    server.rebuild(part_file)
    server.overrides["thing"] = {"count": 9}
    assert "thing" in server.state

    sent = []

    async def go():
        server.queue = asyncio.Queue()
        server.send = lambda payload: sent.append(payload) or asyncio.sleep(0)
        part_file.unlink()
        server.queue.put_nowait(str(part_file))
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(server.drain(), timeout=1.0)

    asyncio.run(go())
    assert "thing" not in server.state
    assert "thing" not in server.overrides  # the sliders go with it
    assert {"type": "gone", "name": "thing"} in sent
