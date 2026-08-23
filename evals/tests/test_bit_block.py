"""Fairness suite for bit_block, the chamfer-dense spec task.

Every flawed solution is a negative control: each flaw must be caught in the stage
built to catch it, and the totals must order the way a user would rank the blocks.
The suite also pins the task's reason to exist: a grid slid far enough into a border
that both chamfers no longer fit does not build at all, which is the OCCT adjacency
limit the task holds the candidate against.
"""

import pathlib

import pytest

from nurb_evals import scoring

EVALS = pathlib.Path(__file__).parents[1]
TASK = EVALS / "tasks" / "bit_block"
SOLUTIONS = pathlib.Path(__file__).parent / "solutions" / "bit_block"

task = scoring.load_task(TASK)

# The reference solutions are written for a 6.5mm shank in five columns, so the tests
# pin the seed that produces one rather than hardcoding a magic number that could
# drift.
SEED = next(
    s
    for s in range(1000)
    if task.instance(s).dims["shank"] == 6.5 and task.instance(s).dims["cols"] == 5
)


@pytest.fixture(scope="module")
def grades():
    names = (
        "good",
        "no_chamfer",
        "hardcoded",
        "hand_grid",
        "shallow",
        "roofed",
        "shifted_grid",
        "bottom_chamfer",
        "notched",
    )
    return {name: scoring.grade(SOLUTIONS / f"{name}.py", TASK, SEED) for name in names}


def test_the_reference_solution_scores_full_marks(grades):
    result = grades["good"]
    assert result["score"] == 1.0, result
    assert result["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 1.0}
    assert result["misfits"] == [] and result["findings"] == []


def test_missing_chamfers_lose_the_finishing_checks(grades):
    result = grades["no_chamfer"]
    assert result["stages"]["dims"] < 1.0
    assert any("lead-in chamfer" in m for m in result["misfits"])
    assert any("top perimeter" in m for m in result["misfits"])


def test_hardcoded_dimensions_are_right_once_and_track_nothing(grades):
    result = grades["hardcoded"]
    assert result["stages"]["dims"] == 1.0
    assert result["stages"]["flex"] == 0.0


def test_a_hand_written_grid_fails_exactly_the_column_probes(grades):
    result = grades["hand_grid"]
    assert result["stages"]["dims"] == 1.0
    assert result["stages"]["flex"] == pytest.approx(1 / 3, abs=1e-3)
    assert all("columns" in p for p in result["flex_problems"])


def test_shallow_pockets_miss_floor_rim_probe_and_volume(grades):
    result = grades["shallow"]
    assert any("floor rim" in m for m in result["misfits"])
    assert any("drop-in" in m for m in result["misfits"])


def test_a_roofed_pocket_never_takes_a_bit(grades):
    """The bounding box, grid, and volume all read right on this one; only the
    drop-in probe stands between a lid and full marks."""
    result = grades["roofed"]
    assert any("drop-in" in m for m in result["misfits"])


def test_a_slid_grid_hides_in_the_bounding_box_but_not_the_borders(grades):
    result = grades["shifted_grid"]
    assert result["stages"]["dims"] < 1.0
    assert any("stated grid" in m for m in result["misfits"])


def test_a_broken_bottom_perimeter_is_charged_by_shape_and_doctrine(grades):
    result = grades["bottom_chamfer"]
    assert any("bottom" in m for m in result["misfits"])
    assert result["stages"]["lint"] < 1.0  # bed_bevel findings agree with the spec


def test_a_notched_footprint_is_not_a_full_rectangular_bottom(grades):
    result = grades["notched"]
    assert any("flat face spanning the full footprint" in m for m in result["misfits"])


def test_the_totals_order_like_a_user_would(grades):
    assert grades["good"]["score"] > grades["hand_grid"]["score"]
    assert grades["hand_grid"]["score"] > grades["hardcoded"]["score"]
    assert grades["hardcoded"]["score"] > grades["shallow"]["score"]


def test_a_grid_slid_into_the_border_does_not_even_build(tmp_path):
    """0.5 of slide leaves a 1.5 border: the pocket lead-in and the perimeter chamfer
    no longer both fit, and OCCT refuses the pass. This is the adjacency limit the
    task is built around; if this ever starts building, the task lost its teeth."""
    source = (SOLUTIONS / "shifted_grid.py").read_text(encoding="utf-8")
    part = tmp_path / "slid_far.py"
    part.write_text(source.replace("web + 0.25 + r", "web + 0.5 + r"), encoding="utf-8")
    result = scoring.grade(part, TASK, SEED)
    assert result["built"] is False
    assert result["score"] == 0.0
