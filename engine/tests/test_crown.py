"""crown() rounds a variable-height rim, or refuses in the part's own words.

Issue #55's biggest ask. The acceptance bar from the research doc: one smooth bead
across a rising and falling roofline, no sliver faces earned, and a doctrine-grade
refusal, naming its own fix, wherever the geometry makes the bead impossible.
"""

import math

from build123d import (
    Plane,
    Polyline,
    Pos,
    Rectangle,
    RectangleRounded,
    Spline,
    extrude,
    make_face,
    offset,
)
import pytest

from nurb import crown
from nurb.crown import WELD

T = 2.4


def ring(plan, height):
    return extrude(plan - offset(plan, -T), height)


def roofline_cut(wall, profile_pts):
    """Cut a roofline into a wall from an XZ profile, across the whole Y span."""
    prof = Polyline(*profile_pts, close=True)
    return wall - extrude(Plane.XZ * make_face(prof.edges()), 100, both=True)


def sine_roofline(amplitude, wavelength):
    """A rounded-rectangle wall whose roofline rises and falls on a spline."""
    wall = ring(RectangleRounded(50, 34, 6), 24)
    pts = [
        (x, 16 + amplitude * math.sin(2 * math.pi * x / wavelength))
        for x in range(-26, 27, 2)
    ]
    curve = Spline(*pts)
    lid = Polyline(pts[-1], (26, 30), (-26, 30), pts[0])
    prof = make_face([curve] + lid.edges())
    return wall - extrude(Plane.XZ * prof, 60, both=True)


def wavy_wall():
    """Gentle enough that the roofline barely tilts across the end walls."""
    return sine_roofline(2, 52)


def test_crowns_a_wavy_rim_into_one_valid_solid():
    wall = wavy_wall()
    out = crown(wall)
    assert out.is_valid
    assert out.volume > wall.volume
    assert not [f for f in out.faces() if f.area < 1.0]  # the bead earns no slivers


def test_the_bead_rides_the_roofline_and_stands_radius_prouder():
    wall = wavy_wall()
    out = crown(wall)
    grew = out.bounding_box().max.Z - wall.bounding_box().max.Z
    assert grew == pytest.approx(T / 2 + WELD, abs=0.05)


def test_a_flush_bead_pokes_only_the_weld_past_the_faces():
    """The interference is what makes the union land; it must stay invisible."""
    wall = wavy_wall()
    out = crown(wall)
    assert out.bounding_box().max.X - wall.bounding_box().max.X == pytest.approx(WELD, abs=0.02)


def test_a_smaller_radius_leaves_shoulders_and_still_builds():
    wall = wavy_wall()
    out = crown(wall, radius=0.6)
    assert out.is_valid
    assert out.bounding_box().max.Z - wall.bounding_box().max.Z == pytest.approx(0.6, abs=0.05)


def test_a_tilted_top_widens_the_weld_and_still_covers_both_edges():
    """A steeper wave tilts the top across the end walls; the bead has to swallow
    the higher edge, so it grows past flush, and never past a fifth of the radius."""
    wall = sine_roofline(5, 34)
    out = crown(wall)
    assert out.is_valid
    assert not [f for f in out.faces() if f.area < 1.0]
    poke = out.bounding_box().max.X - wall.bounding_box().max.X
    assert WELD - 0.02 < poke <= 0.2 * (T / 2) + 0.01


def test_refuses_a_roofline_that_tilts_past_what_the_bead_swallows():
    """Steep waves whose slope peaks right where the roofline crosses the end walls."""
    wall = sine_roofline(6, 24)
    with pytest.raises(ValueError) as exc:
        crown(wall)
    assert "tilts" in str(exc.value)


def test_a_45_degree_ramped_roofline_crowns_cleanly():
    wall = roofline_cut(
        ring(RectangleRounded(50, 34, 6), 24),
        [(-30, 20), (-8, 20), (0, 12), (30, 12), (30, 30), (-30, 30)],
    )
    out = crown(wall)
    assert out.is_valid
    assert not [f for f in out.faces() if f.area < 1.0]


def test_refuses_sharp_plan_corners_and_names_the_fillet_fix():
    wall = ring(Rectangle(50, 34), 20)
    with pytest.raises(ValueError) as exc:
        crown(wall)
    assert "plan fillets of at least" in str(exc.value)


def test_refuses_a_plan_corner_tighter_than_the_bead():
    wall = ring(RectangleRounded(50, 34, 1.0), 20)
    with pytest.raises(ValueError) as exc:
        crown(wall)
    assert "tighter" in str(exc.value)


def test_refuses_a_sheer_roofline_step_and_names_the_ramp_fix():
    wall = roofline_cut(
        ring(RectangleRounded(50, 34, 6), 24),
        [(-30, 20), (0, 20), (0, 12), (30, 12), (30, 30), (-30, 30)],
    )
    with pytest.raises(ValueError) as exc:
        crown(wall)
    assert "Ramp or curve the transition" in str(exc.value)


def test_refuses_a_solid_slab_because_there_is_no_loop():
    """A tray with its floor is the likely mistake: crown the bare wall first."""
    slab = extrude(RectangleRounded(50, 34, 6), 20)
    with pytest.raises(ValueError) as exc:
        crown(slab)
    assert "crown it, then add the rest" in str(exc.value)


def test_refuses_a_wall_that_tapers_in_plan():
    """An off-centre cavity thins one side of the wall: no single centreline exists."""
    wall = extrude(
        RectangleRounded(50, 34, 6) - Pos(0.5, 0) * RectangleRounded(44, 28, 4), 20
    )
    with pytest.raises(ValueError) as exc:
        crown(wall)
    assert "near-constant thickness" in str(exc.value)


def test_refuses_a_radius_wider_than_the_wall():
    wall = wavy_wall()
    with pytest.raises(ValueError) as exc:
        crown(wall, radius=2.0)
    assert "wider than half" in str(exc.value)
