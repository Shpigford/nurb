"""Every rule gets a shape whose answer was worked out by hand, not by running it.

A rule that agrees with itself proves nothing. These are all cases where the expected
finding is obvious from the geometry: a known angle, a known count, a known tip.
"""

from math import tan, radians

from build123d import Box, Cylinder, Plane, Pos, Rot, extrude, Polygon
import pytest

from nurb.checks import FAIL, WARN, Context, run


def only(shape, rule, ctx=None):
    return [f for f in run(shape, ctx, only={rule}) for _ in [1] if f.rule == rule]


# --- overhang ----------------------------------------------------------------


def test_box_has_no_overhang():
    """Six faces, and the only downward one is on the bed."""
    assert only(Box(20, 20, 20), "overhang") == []


def test_flat_ceiling_is_a_90_degree_overhang():
    """A T: the underside of the cap hangs over nothing."""
    shape = Box(6, 6, 20) + Pos(0, 0, 12) * Box(30, 30, 4)
    found = only(shape, "overhang")
    assert len(found) == 1
    assert found[0].value == pytest.approx(90.0)
    assert found[0].severity == FAIL


@pytest.mark.parametrize("angle,flagged", [(30, False), (44, False), (60, True), (75, True)])
def test_sloped_underside_flags_only_past_the_limit(angle, flagged):
    """A wedge whose underside sits at a known angle from vertical."""
    run_out = 20 * tan(radians(angle))
    # Right triangle standing on its point: the hypotenuse from (0,0) up to
    # (run_out, 20) is the underside, and it leans `angle` off vertical by
    # construction.
    section = Plane.XZ * Polygon((0, 0), (0, 20), (run_out, 20), align=None)
    shape = extrude(section, 5, both=True)
    found = only(shape, "overhang")
    assert bool(found) is flagged
    if flagged:
        assert found[0].value == pytest.approx(angle, abs=0.5)


def test_overhang_is_measured_from_the_build_direction_not_model_z():
    """The same solid, printed on a different face, has a different answer.

    This is the trap the Notch parts sit in: they are modelled hanging and printed on
    their backs.
    """
    shape = Box(6, 6, 20) + Pos(0, 0, 12) * Box(30, 30, 4)
    assert only(shape, "overhang") != [], "cap underside hangs over nothing"
    flipped = Context(up=(0, 0, -1))
    assert only(shape, "overhang", flipped) == [], "printed cap-down, nothing hangs"


def test_curved_face_is_sampled_not_guessed():
    """A sphere-like face is fine at its equator and 90 degrees underneath.

    A single normal at the face centre would miss it entirely.
    """
    shape = Pos(0, 0, 20) * Cylinder(8, 6, rotation=(90, 0, 0))
    found = only(shape, "overhang")
    assert found, "the underside of a floating cylinder is an overhang"
    assert found[0].value == pytest.approx(90, abs=1)


# --- stability ---------------------------------------------------------------


def test_box_is_stable():
    assert only(Box(20, 20, 20), "stability") == []


def test_top_heavy_lean_tips():
    """Mass parked well outside a small foot."""
    shape = Box(4, 4, 30) + Pos(20, 0, 28) * Box(20, 20, 4)
    found = only(shape, "stability")
    assert len(found) == 1
    assert found[0].severity == WARN


# --- sliver ------------------------------------------------------------------


def test_sliver_counts_and_the_baseline_silences_it():
    from build123d import chamfer

    shape = Box(20, 20, 20)
    shape = chamfer(shape.edges(), 1)  # three-chamfer corners: 8 tiny triangles
    found = only(shape, "sliver")
    assert len(found) == 1
    count = int(found[0].message.split()[0])
    assert count == 8
    assert only(shape, "sliver", Context(accepted={"sliver": count})) == []
    assert only(shape, "sliver", Context(accepted={"sliver": count - 1})) != []


# --- build volume ------------------------------------------------------------


def test_build_volume_uses_the_best_orientation():
    """300 x 10 x 10 does not fit a 256 bed lying down, but it fits standing up."""
    tall = Box(260, 10, 10)
    assert only(tall, "build_volume", Context(bed=(256, 256, 300))) == [], "stands up"
    assert only(tall, "build_volume", Context(bed=(256, 256, 256))) != [], "260 > 256"
    assert only(tall, "build_volume", Context(bed=(100, 100, 100)))[0].severity == FAIL
