"""stand() turns orientation into geometry, so every rule judges it unchanged.

The facet width is asserted against hand geometry: a square corner tilted 45 degrees
and sunk `facet * sin(90) / 2` deep cuts a flat exactly `facet` wide.
"""

from build123d import Align, Axis, Box, Pos
import pytest

from nurb import stand
from nurb.checks import run


CORNER = (Align.MIN, Align.MIN, Align.MIN)


def bracket():
    """An L: vertical back, horizontal arm at the top. Flat, the arm's underside is a
    90 degree cantilever; stood on the outside of its elbow at 135 about Y, legs up,
    every face is at or under the limit and every region is grounded."""
    back = Box(4, 30, 40, align=CORNER)
    arm = Pos(4, 0, 36) * Box(26, 30, 4, align=CORNER)
    return back + arm


def bed_faces(shape):
    return [f for f in shape.faces() if abs(f.bounding_box().max.Z) < 1e-6]


def test_the_facet_is_exactly_as_wide_as_asked_on_a_square_corner():
    stood = stand(Box(10, 10, 40, align=CORNER), tilt=45, facet=2.0)
    flats = bed_faces(stood)
    assert len(flats) == 1
    assert flats[0].bounding_box().size.X == pytest.approx(2.0, abs=1e-6)
    assert flats[0].bounding_box().size.Y == pytest.approx(10.0, abs=1e-6)


def test_the_result_is_seated_on_the_bed_as_one_solid():
    stood = stand(bracket(), tilt=45, facet=2.0)
    assert len(stood.solids()) == 1
    assert stood.bounding_box().min.Z == pytest.approx(0.0, abs=1e-6)


def test_the_tilt_sign_picks_which_corner_goes_down():
    plus = stand(bracket(), tilt=45, facet=2.0)
    minus = stand(bracket(), tilt=-45, facet=2.0)
    # One stands on the back-bottom corner and leans forward, the other the reverse,
    # so their silhouettes swap which way is long.
    assert plus.bounding_box().size.X > plus.bounding_box().size.Z
    assert minus.bounding_box().size.Z > minus.bounding_box().size.X


def test_a_bracket_that_fails_flat_checks_clean_stood_on_its_elbow():
    """The whole point: the overhang finding is the prompt, stand() is the remedy."""
    flat = [f for f in run(bracket(), only={"overhang"})]
    assert flat and flat[0].value == pytest.approx(90.0)
    # The sign matters and is not guessable from "135": +135 stands this model on the
    # end of its arm, a taller chevron. The V, elbow down, is the negative roll.
    stood = stand(bracket(), tilt=-135, facet=2.0)
    assert run(stood, only={"overhang", "bed_bevel", "stability", "floating"}) == []


def test_standing_on_a_leg_end_leaves_the_other_tip_in_air():
    """The wrong corner: tent pose, elbow up. The tips' faces are all at 45 so the
    overhang rule is silent, and the floating rule is what catches it. Photographed
    before it was a rule: the part built, checked clean and could not print."""
    stood = stand(bracket(), tilt=45, facet=2.0)
    found = [f for f in run(stood, only={"floating"})]
    assert found and all(f.severity == "fail" for f in found)


def test_fins_grow_only_when_the_stance_earns_them():
    """Short on its facet, a part stands alone; past the leverage rule it sprouts a
    fin pad at each side, so its bed contact goes from one strip to three."""
    def strips(shape):
        return [f for f in shape.faces() if abs(f.bounding_box().max.Z) < 1e-6 and f.area >= 4]

    assert len(strips(stand(Box(4, 30, 40, align=CORNER), tilt=45))) == 1
    assert len(strips(stand(Box(4, 30, 80, align=CORNER), tilt=45))) == 3


def test_degenerate_tilts_are_refused():
    for tilt in (0, 90, 180):
        with pytest.raises(ValueError):
            stand(Box(10, 10, 10), tilt=tilt)
    with pytest.raises(ValueError):
        stand(Box(10, 10, 10), facet=0)
    with pytest.raises(ValueError, match="horizontal rotation axis"):
        stand(Box(10, 10, 10), axis=Axis.Z)
