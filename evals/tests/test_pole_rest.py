"""Fairness suite for pole_rest, the curvature function task.

The controls that matter most are the prismatic ones: a V-block and a square channel
both put the pole at exactly the stated height with legal clearance, and both must
lose to the arc gate alone, because rejecting flat answers is this task's reason to
exist. The film control pins the backing probe: an arc traced by an unprintable
shell counts as no support.
"""

import pathlib

import pytest

from nurb_evals import scoring

EVALS = pathlib.Path(__file__).parents[1]
TASK = EVALS / "tasks" / "pole_rest"
SOLUTIONS = pathlib.Path(__file__).parent / "solutions" / "pole_rest"

task = scoring.load_task(TASK)

# The reference solutions are written for a 22.0mm pole at 18.0 axis height, so the
# tests pin the seed that produces one rather than hardcoding a magic number.
SEED = next(
    s
    for s in range(2000)
    if task.instance(s).dims["pole"] == 22.0 and task.instance(s).dims["axis_h"] == 18.0
)


@pytest.fixture(scope="module")
def grades():
    names = (
        "good",
        "polished",
        "v_block",
        "u_channel",
        "tunnel",
        "film",
        "hollow_backing",
        "hardcoded",
        "bulky",
        "short",
    )
    return {name: scoring.grade(SOLUTIONS / f"{name}.py", TASK, SEED) for name in names}


def test_the_reference_cradle_scores_full_marks(grades):
    result = grades["good"]
    assert result["score"] == 1.0, result
    assert result["stages"] == {"lint": 1.0, "dims": 1.0, "flex": 1.0}
    assert result["misfits"] == [] and result["findings"] == []


def test_a_doctrine_polished_cradle_also_scores_full_marks(grades):
    """Every stated gate must survive the polish pass the shipped skill teaches."""
    result = grades["polished"]
    assert result["score"] == 1.0, result


def test_a_v_block_fits_perfectly_and_is_still_not_a_cradle(grades):
    """Two lines of tangent contact, no arc: the prismatic answer this task exists
    to reject. It must lose to the arc gate alone, not to a fit technicality."""
    result = grades["v_block"]
    assert any("not cradled" in m for m in result["misfits"])
    assert not any("does not fit" in m for m in result["misfits"])


def test_a_square_channel_is_not_a_cradle_either(grades):
    result = grades["u_channel"]
    assert any("not cradled" in m for m in result["misfits"])
    assert not any("does not fit" in m for m in result["misfits"])


def test_a_tunnel_cradles_beautifully_and_loses_the_drop_in(grades):
    result = grades["tunnel"]
    assert any("lower straight down" in m for m in result["misfits"])
    assert not any("not cradled" in m for m in result["misfits"])


def test_a_film_arc_has_no_backing(grades):
    """A 0.6mm shell traces the perfect arc; the backing probe reads it as no
    support at all, and the printability rules charge the film on top."""
    result = grades["film"]
    assert any("not cradled" in m for m in result["misfits"])
    assert result["stages"]["lint"] < 1.0


def test_separate_skins_do_not_add_up_to_continuous_backing(grades):
    result = grades["hollow_backing"]
    assert any("not cradled" in m for m in result["misfits"])


def test_hardcoded_dimensions_track_nothing(grades):
    result = grades["hardcoded"]
    assert result["stages"]["dims"] == 1.0
    assert result["stages"]["flex"] == 0.0


def test_bulk_is_charged_only_by_the_ladder(grades):
    result = grades["bulky"]
    assert result["stages"]["flex"] == 1.0
    assert sum("volume" in m for m in result["misfits"]) == 3
    assert not any("cradled" in m or "fit" in m for m in result["misfits"])


def test_a_short_rest_misses_the_stated_length(grades):
    assert any("long along Y" in m for m in grades["short"]["misfits"])


def test_the_totals_order_like_a_user_would(grades):
    assert grades["good"]["score"] > grades["bulky"]["score"]
    assert grades["bulky"]["score"] > grades["tunnel"]["score"]
    assert grades["tunnel"]["score"] > grades["u_channel"]["score"]
    assert grades["u_channel"]["score"] >= grades["v_block"]["score"]
    assert grades["v_block"]["score"] > grades["film"]["score"]
