"""The mesh probe reports dimensions, and compare refuses invented material.

The assertions encode the two lessons from the first real port, a Printables tray
whose bundled STEP carried snap-fit features the shipped meshes never had. The probe
has to recover exact dimensions from tessellation vertices, because they lie on the
true surfaces. And compare's two directions must stay asymmetric: dropped detail is
advisory, added material is a failure, because a rebuild that quietly grows features
is the error averages hide.
"""

import zipfile

import numpy as np
import pytest
from build123d import Box, Cylinder, Pos, Rot

from nurb import builder
from nurb import mesh as meshmod


def plate_with_holes():
    """A 40x30x8 plate with two d6 bores on a 20mm pitch, the probe's bread and butter."""
    body = Box(40, 30, 8)
    for x in (-10, 10):
        body -= Pos(x, 0, 0) * Cylinder(3, 20)
    return body


def test_probe_recovers_planes_and_bores_exactly():
    mesh = builder.to_mesh(plate_with_holes())
    planes, covered = meshmod.planes(mesh)
    offsets = {round(p["offset"], 2) for p in planes}
    # every outer wall of the plate, as |normal . point|
    assert {20.0, 15.0, 4.0} <= offsets

    rounds = meshmod.cylinders(mesh, covered)
    bores = [r for r in rounds if r["concave"] and r["span"] > 270]
    assert len(bores) == 2
    for bore in bores:
        # tessellation vertices sit on the true cylinder, so the fit is exact
        assert bore["radius"] == pytest.approx(3.0, abs=0.01)
        assert bore["axis"] == "Z"
        assert bore["depth"] == pytest.approx(8.0, abs=0.01)
    xs = sorted(b["at"][0] for b in bores)
    assert xs[1] - xs[0] == pytest.approx(20.0, abs=0.02)


def test_pitch_shows_up_in_the_report():
    mesh = builder.to_mesh(plate_with_holes())
    text = "\n".join(meshmod.report("plate", mesh))
    assert "d=6.0 bores along Z: X spacing 20.00" in text


def test_a_wall_profile_with_mixed_arcs_still_yields_the_small_one():
    """A groove next to a big corner round arrives as one connected strip.

    This is the case that defeats a plain fit: the strip's faces share adjacency, so
    a single circle through all of them fits nothing. The curvature split has to get
    the d4 groove back out of it.
    """
    body = Box(40, 30, 10)
    body -= Pos(0, 15, 3) * Rot(0, 90, 0) * Cylinder(2, 40)
    mesh = builder.to_mesh(body)
    planes, covered = meshmod.planes(mesh)
    rounds = meshmod.cylinders(mesh, covered)
    grooves = [r for r in rounds if r["concave"] and abs(r["radius"] - 2.0) < 0.05]
    assert grooves, [round(r["radius"], 2) for r in rounds]
    assert grooves[0]["axis"] == "X"


def test_3mf_loads_without_networkx(tmp_path):
    """trimesh's own 3MF loader wants networkx; ours must not."""
    model = (
        '<?xml version="1.0"?>'
        '<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        '<resources><object id="1" type="model"><mesh>'
        "<vertices>"
        '<vertex x="0" y="0" z="0"/><vertex x="10" y="0" z="0"/>'
        '<vertex x="0" y="10" z="0"/><vertex x="0" y="0" z="10"/>'
        "</vertices><triangles>"
        '<triangle v1="0" v2="2" v3="1"/><triangle v1="0" v2="1" v3="3"/>'
        '<triangle v1="0" v2="3" v3="2"/><triangle v1="1" v2="2" v3="3"/>'
        "</triangles></mesh></object></resources><build/></model>"
    )
    path = tmp_path / "fixture.3mf"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("3D/3dmodel.model", model)
    loaded = meshmod.load(path)
    assert len(loaded) == 1
    _, mesh = loaded[0]
    assert len(mesh.faces) == 4


def test_compare_blesses_a_faithful_rebuild():
    original = builder.to_mesh(plate_with_holes())
    rebuilt = builder.to_mesh(plate_with_holes())
    result = meshmod.compare(rebuilt, original, samples=4000)
    assert result["ok"]
    # the verdict is exact; the displayed tail keeps the sampling floor as noise
    assert float(result["added"].max()) < 3 * result["resolution"]
    assert float(np.median(result["added"])) < result["resolution"]


def test_compare_fails_on_invented_material_however_good_the_averages():
    """A 2mm nub on one wall is the snap-fit feature that never shipped.

    It moves the volume well under a percent, so every average stays clean; only the
    directional check sees it, and it has to fail the run, not annotate it.
    """
    original = builder.to_mesh(Box(40, 30, 8))
    rebuilt = builder.to_mesh(
        Box(40, 30, 8) + Pos(0, 15, 0) * Rot(90, 0, 0) * Cylinder(2, 4)
    )
    result = meshmod.compare(rebuilt, original, samples=4000)
    assert not result["ok"]
    assert float(result["added"].max()) > 1.0
    # the failure points at the nub, not somewhere vague
    assert result["worst_added_at"][1] > 12
    text = "\n".join(meshmod.compare_report("plate", "plate.stl", result))
    assert "invented" in text and "FAIL" in text


def test_compare_treats_dropped_detail_as_advisory_not_failure():
    """The other direction stays a report: a simplified rebuild that only omits
    detail is a judgement call, and blocking it would punish every deliberate
    simplification the docstring discloses."""
    original = builder.to_mesh(
        Box(40, 30, 8) + Pos(0, 15, 0) * Rot(90, 0, 0) * Cylinder(2, 4)
    )
    rebuilt = builder.to_mesh(Box(40, 30, 8))
    result = meshmod.compare(rebuilt, original, samples=4000)
    assert result["ok"]
    assert float(result["dropped"].max()) > 1.0


def test_compare_aligns_by_bed_frame():
    """A mesh exported around a different origin still compares: XY centers and the
    bottom face define the shared frame, the same one the bed does."""
    original = builder.to_mesh(plate_with_holes())
    original.apply_translation([120, -45, 33])
    rebuilt = builder.to_mesh(plate_with_holes())
    result = meshmod.compare(rebuilt, original, samples=4000)
    assert result["ok"]
    assert np.allclose(result["shift"], [120, -45, 33], atol=1e-6)
