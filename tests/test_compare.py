"""The compare loop's contract: the mesh is the ground truth, and the two directions
never blur. A part that grew a boss the original lacks must show up as "part off the
target" even while every target sample sits happily on the part."""

import pytest
import trimesh
from build123d import Box

from nurb import cli, compare
from nurb.server import Server

PART = """from nurb import *

@part
def thing(width=40.0, depth=30.0, height=10.0):
    return Box(width, depth, height)
"""

CARD = """# thing

```toml
target = "scans/original.stl"
```
"""


def test_setting_reads_a_path_or_a_table():
    assert compare.setting({}) is None
    assert compare.setting({"target": "scans/a.stl"}) == ("scans/a.stl", None)
    assert compare.setting({"target": {"file": "a.stl", "units": "in"}}) == ("a.stl", "in")
    with pytest.raises(ValueError):
        compare.setting({"target": 3})


def test_identical_geometry_measures_zero_both_ways():
    metrics = compare.against(Box(40, 30, 10), trimesh.creation.box(extents=[40, 30, 10]))
    assert metrics["part"]["max"] < 0.05
    assert metrics["target"]["max"] < 0.05


def test_a_size_difference_is_visible_and_bounded():
    # The part is 10mm taller: its extra skin sits up to 5mm off the target after
    # centering, and the target's top face lies 5mm inside the part, which is surface
    # the part equally fails to reproduce. Both directions must say so.
    metrics = compare.against(Box(40, 30, 20), trimesh.creation.box(extents=[40, 30, 10]))
    assert metrics["part"]["max"] == pytest.approx(5.0, abs=0.3)
    assert metrics["target"]["max"] == pytest.approx(5.0, abs=0.3)


def test_a_translated_target_is_centered_before_measuring():
    mesh = trimesh.creation.box(extents=[40, 30, 10])
    mesh.apply_translation([100.0, -50.0, 25.0])
    metrics = compare.against(Box(40, 30, 10), mesh)
    assert metrics["part"]["max"] < 0.05
    # Box() sits centered at the origin, so the offset is the translation undone.
    assert metrics["offset"] == [-100.0, 50.0, -25.0]


def project(tmp_path):
    (tmp_path / "parts").mkdir()
    (tmp_path / "parts" / "thing.py").write_text(PART)
    (tmp_path / "parts" / "thing.md").write_text(CARD)
    (tmp_path / "scans").mkdir()
    trimesh.creation.box(extents=[40, 30, 10]).export(tmp_path / "scans" / "original.stl")
    return Server(tmp_path)


def test_rebuild_attaches_the_cards_target(tmp_path):
    server = project(tmp_path)
    entry = server.rebuild(tmp_path / "parts" / "thing.py")
    assert entry["target"]["file"] == "scans/original.stl"
    assert entry["target"]["offset"] == [0.0, 0.0, 0.0]
    assert entry["target_glb"][:4] == b"glTF"
    # The GLB is served, never wired: a scan is megabytes and the socket is JSON.
    assert "target_glb" not in server._meta(entry)


def test_check_adds_the_deviation_and_reuses_the_loaded_mesh(tmp_path):
    server = project(tmp_path)
    server.rebuild(tmp_path / "parts" / "thing.py")
    held = server.targets[("scans/original.stl", None)]
    entry = server.check(tmp_path / "parts" / "thing.py")
    assert entry["target"]["metrics"]["part"]["max"] < 0.05
    assert entry["target"]["metrics"]["target"]["max"] < 0.05
    assert server.targets[("scans/original.stl", None)] is held


def test_target_units_version_the_viewers_cached_geometry(tmp_path):
    server = project(tmp_path)
    millimetres = server._target_mesh("scans/original.stl", "mm")
    metres = server._target_mesh("scans/original.stl", "m")
    assert millimetres["stamp"] != metres["stamp"]
    assert metres["mesh"].extents.max() == pytest.approx(
        millimetres["mesh"].extents.max() * 1000
    )


def test_compare_command_walks_the_cards_variants(tmp_path, monkeypatch, capsys):
    project(tmp_path)
    card = CARD.replace(
        "```\n",
        "\n[variants.narrow.params]\nwidth = 20.0\n```\n",
    )
    (tmp_path / "parts" / "thing.md").write_text(card)
    monkeypatch.chdir(tmp_path)

    cli.main(["compare", "thing"])

    output = capsys.readouterr().out
    assert "thing against scans/original.stl" in output
    assert "narrow against scans/original.stl" in output


def test_viewer_discards_a_ghost_loaded_for_a_replaced_mesh_group():
    from nurb import server as server_mod

    viewer = server_mod.VIEWER.read_text(encoding="utf-8")
    ghost = viewer.split("async function ghostAttach", 1)[1].split(
        "// ---- axis triad ----", 1
    )[0]
    assert "const group = mesh;" in ghost
    assert "mesh !== group" in ghost
    assert "group.add(g);" in ghost


def test_a_missing_target_file_reports_instead_of_breaking_the_build(tmp_path):
    server = project(tmp_path)
    (tmp_path / "scans" / "original.stl").unlink()
    entry = server.rebuild(tmp_path / "parts" / "thing.py")
    assert entry["error"] is None
    assert "no file at" in entry["target"]["error"]
