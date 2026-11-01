"""The compare loop's contract: the mesh is the ground truth, and the two directions
never blur. A part that grew a boss the original lacks must show up as "part off the
target" even while every target sample sits happily on the part."""

import pytest
import trimesh
from build123d import Box

from nurb import compare

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
    return tmp_path
