"""The export route is the configurator's back end: what the sliders hold, polished."""

import asyncio
import io

import pytest
import trimesh

from nurb.server import Server

PART = """from nurb import *

@part
def thing(width=40.0, depth=30.0, height=5.0):
    return Box(width, depth, height)
"""


def project(tmp_path):
    (tmp_path / "parts").mkdir()
    part = tmp_path / "parts" / "thing.py"
    part.write_text(PART)
    server = Server(tmp_path)
    server.rebuild(part)
    return server


def test_export_builds_at_the_slider_values(tmp_path):
    server = project(tmp_path)
    server.overrides["thing"] = {"width": 15.0}
    resp = asyncio.run(server.export("thing.stl"))
    assert resp.status_code == 200
    assert resp.headers["Content-Disposition"] == 'attachment; filename="thing.stl"'
    mesh = trimesh.load(io.BytesIO(resp.body), file_type="stl")
    assert mesh.extents == pytest.approx([15.0, 30.0, 5.0])
    assert mesh.is_watertight


def test_export_writes_step_too(tmp_path):
    resp = asyncio.run(project(tmp_path).export("thing.step"))
    assert resp.status_code == 200
    assert resp.body.startswith(b"ISO-10303-21")


def test_export_refuses_what_it_cannot_serve(tmp_path):
    server = project(tmp_path)
    assert asyncio.run(server.export("missing.stl")).status_code == 404
    assert asyncio.run(server.export("thing.gcode")).status_code == 404
