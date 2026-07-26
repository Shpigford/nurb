"""The example parts are the calibration set, so the suite asserts against them.

Every number here was recorded by hand in Fusion before nurb existed. They are worth
more than a synthetic fixture: a rule that reproduces a figure someone measured off a
different kernel months ago is a rule that is measuring the right thing.
"""

import pathlib

import pytest

from nurb import builder, checks

PARTS = pathlib.Path(__file__).parents[1] / "examples" / "notch" / "parts"


def build(name, **overrides):
    return builder.build(PARTS / f"{name}.py", overrides=overrides or None)[0]


def findings(name, shape=None):
    shape = shape if shape is not None else build(name)
    return checks.run(shape, checks.from_card(PARTS / f"{name}.py"))


@pytest.mark.parametrize("name", ["hook_scissors", "shelf_gridfinity", "fit_coupon"])
def test_every_example_is_one_solid_and_reports_clean(name):
    """The credibility bar: nothing fires on a part that has printed fine."""
    shape = build(name)
    assert len(shape.solids()) == 1
    assert findings(name, shape) == []


@pytest.mark.parametrize(
    "name,size",
    [("hook_scissors", (34.0, 25.16, 30.0)), ("shelf_gridfinity", (94.0, 100.64, 42.0))],
)
def test_bounding_boxes_match_the_fusion_originals(name, size):
    got = build(name).bounding_box().size
    assert (got.X, got.Y, got.Z) == pytest.approx(size, abs=1e-3)


@pytest.mark.parametrize("name,count", [("hook_scissors", 6), ("shelf_gridfinity", 18)])
def test_sliver_baselines_are_what_the_cards_claim(name, count):
    shape = build(name)
    assert len([f for f in shape.faces() if f.area < 1.0]) == count


@pytest.mark.parametrize(
    "grid_x,grid_y,brackets", [(1, 2, 3), (2, 2, 4), (3, 2, 6), (2, 3, 4)]
)
def test_the_shelf_sliver_baseline_generalizes(grid_x, grid_y, brackets):
    """4 per cell plus the two corner triangles, at every grid the card names."""
    shape = build("shelf_gridfinity", grid_x=grid_x, grid_y=grid_y, bracket_count=brackets)
    small = [f for f in shape.faces() if f.area < 1.0]
    assert len(small) == 4 * grid_x * grid_y + 2


def test_channel_floors_land_on_pitch(name="shelf_gridfinity"):
    shape = build(name)
    floors = sorted(
        round(f.center().Y, 4)
        for f in shape.faces()
        if abs(f.bounding_box().min.X + 4.2) < 1e-3 and abs(f.bounding_box().max.X + 4.2) < 1e-3
    )
    assert floors == [round(k * 25.16, 4) for k in range(4)]


def test_projection_ratio_reproduces_the_number_on_the_card():
    """The card says grid_y 3 is a ratio of 3.2 at item_height 42, and 55 fixes it."""
    deep = findings("shelf_gridfinity", build("shelf_gridfinity", grid_y=3))
    ratio = [f for f in deep if f.rule == "projection_ratio"]
    assert len(ratio) == 1
    assert ratio[0].value == pytest.approx(3.24, abs=0.01)

    taller = findings(
        "shelf_gridfinity", build("shelf_gridfinity", grid_y=3, item_height=55)
    )
    assert [f for f in taller if f.rule == "projection_ratio"] == []


def test_a_part_that_does_not_cantilever_opts_out():
    shape = build("hook_scissors")
    assert checks.run(shape, checks.Context(), only={"projection_ratio"}) == []


def test_the_two_piece_guard_still_fires():
    """Phase 1's High finding, pinned so it cannot come back."""
    with pytest.raises(ValueError, match="item_depth"):
        build("hook_scissors", item_depth=5.0)
