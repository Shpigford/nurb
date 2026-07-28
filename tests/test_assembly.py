"""Assemblies: the sweep must find the jam the printability rules cannot see.

The fixture geometry is chosen so the jam angle is analytic, not observed: a flap
hinged along the edge of a slab it lies flat against can rise and swing over its own
hinge, and the first material interference is at exactly 180 degrees, when its
trailing face crosses into the slab's quadrant. Downward it interferes immediately.
No tolerance in these tests was tuned to make them pass.
"""

import pathlib

import pytest

from nurb import builder, checks

FLAP_ASM = '''from nurb import *


@assembly
def rig(open_deg=0.0, wall=True):
    slab = Pos(0, 15, -1) * Box(20, 30, 2)
    flap = Pos(0, 15, 1) * Box(20, 30, 2)
    flap = hinge(flap, Axis((0, 0, 0), (1, 0, 0)), through=(-90, 270), at=open_deg,
                 name="flap")
    if not wall:
        return (flap,)
    return slab, flap
'''

PLATE = '''from nurb import *


@part
def plate(width=10.0, draft=False):
    return Box(width, 10, 2)
'''

USE_ASM = '''from nurb import *


@assembly
def carrier(open_deg=0.0):
    base = Pos(0, 0, -5) * Box(40, 40, 2)
    arm = use("plate")
    arm = hinge(Pos(0, 10, 0) * arm, Axis((0, 5, 0), (1, 0, 0)), through=(0, 90),
                at=open_deg, name="arm")
    return base, arm
'''


@pytest.fixture
def project(tmp_path):
    (tmp_path / "parts").mkdir()
    return tmp_path


def write(project, name, text):
    path = project / "parts" / f"{name}.py"
    path.write_text(text)
    return path


def motion(shape):
    return [f for f in checks.run(shape) if f.rule == "motion"]


def test_an_assembly_builds_to_one_compound_the_existing_pipeline_can_carry(project):
    path = write(project, "rig", FLAP_ASM)
    shape, params, _ = builder.build(path)
    assert shape.volume > 0
    assert [p["name"] for p in params] == ["open_deg", "wall"]
    # The whole point of returning a Compound: to_glb and stats need no new code.
    assert builder.to_glb(shape)
    assert builder.stats(shape)["bbox"][0] == pytest.approx(20, abs=0.1)


def test_the_sweep_finds_the_analytic_jam_in_both_directions(project):
    path = write(project, "rig", FLAP_ASM)
    shape, _, _ = builder.build(path)
    found = motion(shape)
    assert len(found) == 2
    up = max(f.value for f in found)
    down = min(f.value for f in found)
    # Rising, the flap swings over the hinge and its trailing face crosses into the
    # slab's quadrant at exactly 180. Falling, it presses into the slab at once.
    assert up == pytest.approx(180.0, abs=0.2)
    assert down == pytest.approx(0.0, abs=0.2)
    for f in found:
        assert f.severity == checks.FAIL
        assert f.where is not None
        assert "flap" in f.message


def test_lying_flat_against_the_slab_is_tangent_and_tangent_is_clear(project):
    """Zero-volume contact is not a collision, the same way a fit is not a weld."""
    path = write(project, "rig", FLAP_ASM)
    shape, _, _ = builder.build(path)
    found = motion(shape)
    assert all("before it moves" not in f.message for f in found)


def test_without_the_wall_the_whole_range_is_clear(project):
    path = write(project, "rig", FLAP_ASM)
    shape, _, _ = builder.build(path, overrides={"wall": False})
    assert motion(shape) == []


def test_a_pose_already_inside_the_wall_is_its_own_finding(project):
    path = write(project, "rig", FLAP_ASM)
    shape, _, _ = builder.build(path, overrides={"open_deg": -30.0})
    found = motion(shape)
    assert len(found) == 1
    assert "before it moves" in found[0].message


def test_use_builds_a_sibling_part_and_the_scene_carries_it(project):
    write(project, "plate", PLATE)
    path = write(project, "carrier", USE_ASM)
    shape, _, _ = builder.build(path)
    scene = shape._nurb_scene
    assert [h.name for h in scene.hinges] == ["arm"]
    assert len(scene.statics) == 1
    # 0..90 with the base 5mm below the hinge: nothing in the way going up.
    assert motion(shape) == []


def test_a_hinged_solid_that_is_not_returned_is_an_error_not_a_silence(project):
    path = write(
        project,
        "broken",
        FLAP_ASM.replace("return slab, flap", "return (slab,)"),
    )
    with pytest.raises(Exception, match="not.*returned|returned.*not"):
        builder.build(path)


def test_printability_rules_stay_off_assemblies(project):
    """An assembled scene would fail overhang and min_wall for reasons that mean
    nothing: each part already answered those alone."""
    path = write(project, "rig", FLAP_ASM)
    shape, _, _ = builder.build(path)
    assert all(f.rule == "motion" for f in checks.run(shape))
