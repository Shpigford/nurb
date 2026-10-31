"""The stepped counterbore cutter, probed where each step is supposed to be.

The rule-facing cases live in test_rules.py; these pin the cutter's own geometry: the
two bridge steps really are perpendicular slots, the shaft runs the whole way, and the
mouth leads past its own origin so a flush seat still cuts.
"""

from build123d import Align, Box, Pos
import pytest

from nurb import counterbore


def plate_with(cutter):
    plate = Box(30, 30, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return (plate - cutter).solids()[0]


def test_the_steps_are_perpendicular_slots():
    """M3-ish: 3.4 hole, 6.2 pocket 3 deep, so step one spans y only and step two x
    only. Probed at 2.9mm out, inside the pocket circle but outside both slot widths."""
    solid = plate_with(counterbore(hole_dia=3.4, head_dia=6.2, head_depth=3, depth=12))

    def void(x, y, z):
        return not solid.is_inside((x, y, z))

    assert void(0, 0, 1) and void(0, 0, 5) and void(0, 0, 9), "the shaft runs the whole way"
    assert void(2.9, 0, 1) and void(0, 2.9, 1), "the head pocket is 6.2 wide"
    assert void(2.9, 0, 3.5) and not void(0, 2.9, 3.5), "step one is a slot across x"
    assert void(0, 2.9, 4.5) and not void(2.9, 0, 4.5), "step two is the same slot across y"
    assert not void(2.9, 0, 5.5) and not void(0, 2.9, 5.5), "above the steps, only the shaft"


def test_the_mouth_leads_past_its_origin():
    """Seated flush on a bottom face, the cut must not depend on a coplanar boolean."""
    assert counterbore(3.4, 6.2, 3, 12).bounding_box().min.Z == pytest.approx(-1.0)


def test_a_generous_depth_is_harmless():
    """The doctrine's way to cut a through hole: ask for more than the part."""
    solid = plate_with(counterbore(3.4, 6.2, 3, 40))
    assert not solid.is_inside((0, 0, 9.9))
    assert solid.volume > 0


def test_a_head_no_wider_than_the_hole_is_refused():
    with pytest.raises(ValueError, match="wider than its hole"):
        counterbore(hole_dia=5, head_dia=4, head_depth=2, depth=10)


def test_a_depth_the_pocket_and_steps_swallow_is_refused():
    with pytest.raises(ValueError, match="leaves no hole"):
        counterbore(hole_dia=3, head_dia=6, head_depth=3, depth=4)


def test_dimensions_must_be_positive():
    with pytest.raises(ValueError, match="positive"):
        counterbore(hole_dia=3, head_dia=6, head_depth=0, depth=10)
