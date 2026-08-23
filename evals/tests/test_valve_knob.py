"""Fairness suite for valve_knob, the mating-fit task.

The tolerance band is graded from both sides, so the suite holds a bore that is too
tight and a bore that rattles, and each must lose exactly its own gate. The round
bore is the control that matters most: it fits the stem perfectly and transmits no
torque, which only the twisted-stem drive can know.
"""

import pathlib

import pytest

from nurb_evals import scoring

EVALS = pathlib.Path(__file__).parents[1]
TASK = EVALS / "tasks" / "valve_knob"
SOLUTIONS = pathlib.Path(__file__).parent / "solutions" / "valve_knob"

task = scoring.load_task(TASK)

# The reference solutions are written for an 8.0mm stem with a 6.5mm across-flat, so
# the tests pin the seed that produces one rather than hardcoding a magic number.
SEED = next(
    s
    for s in range(2000)
    if task.instance(s).dims["shaft"] == 8.0 and task.instance(s).dims["flat"] == 6.5
)


@pytest.fixture(scope="module")
def grades():
    names = (
        "good",
        "polished",
        "round_bore",
        "tight",
        "sloppy",
        "no_grip",
        "wrong_flat",
        "hardcoded",
        "bulky",
    )
    return {name: scoring.grade(SOLUTIONS / f"{name}.py", TASK, SEED) for name in names}


def test_the_reference_knob_scores_full_marks(grades):
    result = grades["good"]
    assert result["score"] == 1.0, result
    assert result["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 1.0}
    assert result["misfits"] == [] and result["findings"] == []


def test_a_doctrine_polished_knob_also_scores_full_marks(grades):
    """Every stated gate must survive the polish pass the shipped skill teaches."""
    result = grades["polished"]
    assert result["score"] == 1.0, result


def test_a_round_bore_fits_and_transmits_no_torque(grades):
    """The stem slides in at the right clearance and spins forever: only the
    twisted-stem drive can tell this bore from a real one."""
    result = grades["round_bore"]
    assert any("no torque" in m for m in result["misfits"])
    assert not any("does not fit" in m or "rattles" in m for m in result["misfits"])


def test_a_tight_bore_jams_the_grown_stem(grades):
    result = grades["tight"]
    assert any("does not fit" in m for m in result["misfits"])
    assert not any("rattles" in m for m in result["misfits"])


def test_a_loose_bore_rattles(grades):
    result = grades["sloppy"]
    assert any("rattles" in m for m in result["misfits"])
    assert not any("does not fit" in m or "no torque" in m for m in result["misfits"])


def test_a_round_puck_has_nothing_to_grip(grades):
    result = grades["no_grip"]
    assert any("nothing to grip" in m for m in result["misfits"])
    assert not any("does not fit" in m for m in result["misfits"])


def test_the_flat_faces_the_stated_way(grades):
    assert any("does not fit" in m for m in grades["wrong_flat"]["misfits"])


def test_hardcoded_dimensions_track_nothing(grades):
    result = grades["hardcoded"]
    assert result["stages"]["dims"] == 1.0
    assert result["stages"]["flex"] == 0.0


def test_bulk_is_charged_only_by_the_ladder(grades):
    result = grades["bulky"]
    assert result["stages"]["flex"] == 1.0
    assert sum("volume" in m for m in result["misfits"]) == 2
    assert not any("fit" in m or "torque" in m or "grip" in m for m in result["misfits"])


def test_the_totals_order_like_a_user_would(grades):
    assert grades["good"]["score"] > grades["bulky"]["score"]
    assert grades["bulky"]["score"] > grades["sloppy"]["score"]
    assert grades["sloppy"]["score"] > grades["round_bore"]["score"]
