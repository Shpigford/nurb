"""A scan is read in millimetres whatever units its exporter wrote.

The fixture is what a phone actually hands over: an open sheet, not a solid, in
metres, because that is what Scaniverse and Polycam export. The profile is a known
staircase so the section has exact numbers to recover.
"""

import numpy as np
import pytest
import trimesh

from nurb import cli, scan

# (depth, height) in metres: two 10mm courses with a 4mm step between them.
PROFILE = [
    (0.0, 0.0),
    (0.0, 0.010),
    (0.004, 0.010),
    (0.004, 0.020),
    (0.0, 0.020),
    (0.0, 0.030),
]


def sheet(tmp_path, name="siding.ply"):
    prof = np.asarray(PROFILE)
    n = len(prof)
    near = np.column_stack([np.zeros(n), prof[:, 0], prof[:, 1]])
    far = near.copy()
    far[:, 0] = 0.3
    faces = []
    for i in range(n - 1):
        faces += [(i, i + 1, n + i + 1), (i, n + i + 1, n + i)]
    mesh = trimesh.Trimesh(vertices=np.vstack([near, far]), faces=faces)
    target = tmp_path / name
    mesh.export(target)
    return target


def test_a_metre_scale_mesh_is_read_as_metres(tmp_path):
    mesh, unit, source = scan.load(sheet(tmp_path))
    assert (unit, source) == ("m", "guess")
    assert mesh.extents.max() == pytest.approx(300.0, abs=0.01)


def test_a_millimetre_mesh_stays_millimetres(tmp_path):
    target = tmp_path / "box.stl"
    trimesh.creation.box(extents=(40, 20, 10)).export(target)
    mesh, unit, source = scan.load(target)
    assert (unit, source) == ("mm", "guess")
    assert mesh.extents.max() == pytest.approx(40.0)


def test_an_explicit_unit_beats_the_guess(tmp_path):
    target = tmp_path / "box.stl"
    trimesh.creation.box(extents=(40, 20, 10)).export(target)
    mesh, unit, source = scan.load(target, units="cm")
    assert (unit, source) == ("cm", "argument")
    assert mesh.extents.max() == pytest.approx(400.0)


def test_glb_declares_metres_even_when_it_is_over_ten_units_across(tmp_path):
    """A room-sized GLB must not fall through to the size heuristic and shrink 1,000x."""
    target = tmp_path / "room.glb"
    target.write_bytes(
        trimesh.Scene([trimesh.creation.box(extents=(12, 4, 3))]).export(
            file_type="glb"
        )
    )
    mesh, unit, source = scan.load(target)
    assert (unit, source) == ("m", "file")
    assert mesh.extents.max() == pytest.approx(12_000.0)
    assert "declared by the file format" in scan.report(target.name, mesh, unit, source)[1]


def test_split_glb_vertices_are_welded_before_the_surface_report(tmp_path):
    """Normal and UV seams do not turn a geometrically closed GLB into an open scan."""
    box = trimesh.creation.box(extents=(0.04, 0.02, 0.01))
    vertices = box.triangles.reshape((-1, 3))
    split = trimesh.Trimesh(
        vertices=vertices,
        faces=np.arange(len(vertices)).reshape((-1, 3)),
        process=False,
    )
    target = tmp_path / "closed.glb"
    target.write_bytes(trimesh.Scene([split]).export(file_type="glb"))
    mesh, unit, source = scan.load(target)
    assert mesh.is_watertight
    assert "watertight" in scan.report(target.name, mesh, unit, source)[0]


def test_a_section_recovers_the_profile(tmp_path):
    mesh, _, _ = scan.load(sheet(tmp_path))
    cut = scan.section(mesh, "x")
    assert cut["plane"] == ("y", "z")
    assert len(cut["profiles"]) == 1
    prof = cut["profiles"][0]
    assert not prof["closed"]
    points = prof["points"]
    # The staircase comes back as its own corners: the step depth and the reveals.
    assert points[:, 0].max() == pytest.approx(4.0, abs=0.05)
    assert points[:, 1].min() == pytest.approx(0.0, abs=0.05)
    assert points[:, 1].max() == pytest.approx(30.0, abs=0.05)
    assert len(points) == len(PROFILE)


def test_a_solid_sections_to_a_closed_loop(tmp_path):
    target = tmp_path / "box.stl"
    trimesh.creation.box(extents=(40, 20, 10)).export(target)
    mesh, _, _ = scan.load(target)
    cut = scan.section(mesh, "z:0.5")
    assert cut["pos"] == pytest.approx(0.0)
    assert cut["profiles"][0]["closed"]
    assert cut["profiles"][0]["length"] == pytest.approx(120.0, abs=0.1)


def test_an_absolute_position_is_in_the_scans_own_frame(tmp_path):
    mesh, _, _ = scan.load(sheet(tmp_path))
    cut = scan.section(mesh, "z:5mm")
    assert cut["pos"] == pytest.approx(5.0)
    # 5mm up is inside the lower course, where the sheet sits at depth 0.
    assert cut["profiles"][0]["points"][:, 1].max() == pytest.approx(0.0, abs=0.05)


def test_a_bad_section_spec_names_the_grammar(tmp_path):
    mesh, _, _ = scan.load(sheet(tmp_path))
    with pytest.raises(ValueError, match="AXIS"):
        scan.section(mesh, "q")


def test_a_point_cloud_names_the_fix(tmp_path):
    """A gaussian-splat export is the likeliest first-scan mistake."""
    target = tmp_path / "splat.ply"
    trimesh.PointCloud(np.random.default_rng(1).random((50, 3))).export(target)
    with pytest.raises(ValueError, match="OBJ, STL or GLB"):
        scan.load(target)


def test_a_missing_file_is_a_clean_error(tmp_path):
    with pytest.raises(ValueError, match="no file"):
        scan.load(tmp_path / "missing.ply")


def test_the_command_needs_no_project(tmp_path, monkeypatch, capsys):
    """The scan arrives before the part exists, so scanning must work anywhere."""
    target = sheet(tmp_path)
    monkeypatch.chdir(tmp_path)
    cli.main(["scan", str(target), "--section", "x"])
    out = capsys.readouterr().out
    assert "read as metres" in out
    assert "points are (y, z) in mm" in out
    assert "(    4.00,    10.00)" in out
