"""Every rule gets a shape whose answer was worked out by hand, not by running it.

A rule that agrees with itself proves nothing. These are all cases where the expected
finding is obvious from the geometry: a known angle, a known count, a known tip.
"""

from math import cos, radians, sin, tan

from build123d import Align, Axis, Box, Cylinder, Plane, Pos, Rot, extrude, Polygon
import pytest

from nurb import supports
from nurb.checks import FAIL, NOTE, WARN, Context, run
from nurb.orient import stand


def only(shape, rule, ctx=None):
    return [f for f in run(shape, ctx, only={rule}) for _ in [1] if f.rule == rule]


# --- solids ------------------------------------------------------------------


def test_one_body_is_one_part():
    assert only(Box(20, 20, 20), "solids") == []


def test_two_loose_bodies_are_not_a_part():
    """Two boxes with clear air between them. Nothing joins them, so nothing does."""
    shape = Box(20, 20, 10) + Pos(40, 0, 0) * Box(20, 20, 10)
    found = only(shape, "solids")
    assert len(found) == 1
    assert found[0].severity == FAIL
    assert found[0].value == 2


def test_tangent_contact_is_still_two_pieces():
    """A shelf touching its post along one line reads as joined and is not.

    This is the case the rule exists for: from every angle in the viewer the part looks
    whole, and the kernel has kept it as two bodies the whole time.
    """
    post = Cylinder(8, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shelf = Pos(8 + 15, 0, 20) * Box(30, 20, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    assert only(post + shelf, "solids")


def test_a_part_in_pieces_silences_the_other_rules():
    """One finding that names the fault, not five describing its symptoms.

    The tangent shelf reports floating tips and a 90 degree overhang as well, all true
    of one fragment and all beside the point until the join exists.
    """
    post = Cylinder(8, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shelf = Pos(8 + 15, 0, 20) * Box(30, 20, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    found = run(post + shelf)
    assert [f.rule for f in found] == ["solids"]


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

    Notch happens to print exactly as modelled, so its build direction is +z. Nothing
    guarantees that in general, and a rule that assumes it does not error when it is
    wrong, it just reports confident nonsense.
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


def test_a_narrow_flat_foot_still_uses_its_center_of_mass():
    """A slim rectangular foot is ordinary bed contact, not a diagonal facet."""
    corner = (Align.MIN, Align.CENTER, Align.MIN)
    shape = Box(4, 30, 20, align=corner) + Pos(2, 0, 16) * Box(
        20, 30, 4, align=corner
    )
    assert len(shape.solids()) == 1
    found = only(shape, "stability")
    assert len(found) == 1
    assert found[0].severity == WARN


def test_standing_on_a_facet_holds_by_adhesion_not_balance():
    """A part stood at 45 always has its centre of mass outside the facet, so the
    centre-of-mass test would warn on every diagonal print, including the bracket
    this was calibrated against, which printed clean."""
    from nurb import stand

    assert only(stand(Box(4, 30, 30), tilt=45, facet=2.0), "stability") == []


def test_standing_too_tall_on_a_facet_is_the_fin_signal():
    """With fins declined, the rule is the referee for hand-tilted geometry."""
    from nurb import stand

    found = only(stand(Box(4, 30, 80), tilt=45, facet=2.0, fins=False), "stability")
    assert len(found) == 1
    assert found[0].severity == WARN
    assert "fin" in found[0].message


def test_grown_fins_satisfy_every_rule_but_their_declared_slivers():
    """The generated fin is one solid with the part, grounded, bridged at its tines,
    thick enough for min_wall, and standing on pad strips that widen the stance past
    the leverage rule. The tines' tiny faces are the one honest cost, and those are
    declared on a card like any other earned sliver."""
    from nurb import stand

    finned = stand(Box(4, 30, 80), tilt=45, facet=2.0)
    assert len(finned.solids()) == 1
    assert only(finned, "stability") == []
    assert only(finned, "floating") == []
    assert only(finned, "overhang") == []
    assert only(finned, "min_wall") == []


def test_grown_fins_clear_the_stability_rule_on_a_tall_part():
    """The fin pads widen the whole footprint; their own short edge is not the stance."""
    from nurb import stand

    finned = stand(Box(4, 30, 160), tilt=45, facet=2.0)
    assert only(finned, "stability") == []


# --- warp risk ---------------------------------------------------------------


def test_a_big_plate_with_sharp_corners_will_curl():
    """The 300 x 150 shelf that lifted all four corners off the bed: a 45,000mm2
    first layer with each corner holding on at a point."""
    found = only(Box(300, 150, 5), "warp_risk")
    assert len(found) == 1
    assert found[0].severity == WARN
    assert found[0].value == 4


def test_a_polish_chamfer_is_not_corner_relief():
    """A 1mm chamfer moves the point half a millimetre; the outline still turns its
    full 90 degrees within a couple of millimetres and still peels."""
    from build123d import chamfer

    plate = chamfer(Box(300, 150, 5).edges().filter_by(Axis.Z), 1.0)
    assert len(only(plate, "warp_risk")) == 1


def test_rounded_corners_spread_the_peel_and_clear_it():
    from build123d import fillet

    plate = fillet(Box(300, 150, 5).edges().filter_by(Axis.Z), 8.0)
    assert only(plate, "warp_risk") == []


def test_an_undersized_round_is_still_a_peel_point():
    from build123d import fillet

    plate = fillet(Box(300, 150, 5).edges().filter_by(Axis.Z), 6.0)
    assert len(only(plate, "warp_risk")) == 1


def test_warp_risk_uses_a_non_axis_aligned_build_direction():
    """Changing coordinates does not change the plate or make its footing disappear."""
    plate = Rot(0, 45, 0) * Box(300, 150, 5)
    diagonal = sin(radians(45)), 0, cos(radians(45))
    found = only(plate, "warp_risk", Context(up=diagonal))
    assert len(found) == 1
    assert found[0].value == 4


def test_a_small_first_layer_never_warps():
    """Sharp corners and all: 10,000mm2 is what adhesion holds without help."""
    assert only(Box(100, 100, 5), "warp_risk") == []


def test_a_ribbed_floor_contracts_too_little_to_peel():
    """The same 300 x 150 plate lifted onto ribs: the first layer is the rib
    bottoms, skinny rectangles full of sharp corners that each pull too little."""
    floor = Pos(0, 0, 3.5) * Box(300, 150, 3)
    ribbed = sum((Pos(x, 0, 1) * Box(3, 150, 2) for x in range(-135, 150, 30)), floor)
    assert only(ribbed, "warp_risk") == []


def test_a_shrinky_material_tightens_the_warp_threshold():
    """The 100mm plate that PLA holds down: ABS contracts five times as much, so
    the same pull arrives off a fifth of the area, and the finding says which
    plastic to blame."""
    plate = Box(100, 100, 5)
    assert only(plate, "warp_risk") == []
    found = only(plate, "warp_risk", Context(material="abs"))
    assert len(found) == 1
    assert "ABS" in found[0].message


def test_a_shrinky_material_scales_the_face_threshold_too():
    """An 8,100mm2 ABS plate is past its 4,000mm2 threshold even though it is
    smaller than half the unscaled PLA threshold."""
    found = only(Box(90, 90, 5), "warp_risk", Context(material="abs"))
    assert len(found) == 1
    assert found[0].value == 4


def test_petg_judges_as_pla():
    assert only(Box(100, 100, 5), "warp_risk", Context(material="petg")) == []


# --- pin ---------------------------------------------------------------------

SEAT = (Align.CENTER, Align.CENTER, Align.MIN)


def test_a_thin_pin_may_not_print_at_all():
    """2.5mm across: the nozzle re-melts each ring as it lays the next."""
    shape = Box(20, 20, 4) + Pos(0, 0, 2) * Cylinder(1.25, 10, align=SEAT)
    found = only(shape, "pin")
    assert len(found) == 1
    assert found[0].severity == FAIL
    assert found[0].value == 2.5


def test_a_pin_under_5mm_is_perimeter_only():
    """4mm across prints, but as a tube with nothing inside, weakest at its base."""
    shape = Box(20, 20, 4) + Pos(0, 0, 2) * Cylinder(2, 12, align=SEAT)
    found = only(shape, "pin")
    assert len(found) == 1
    assert found[0].severity == WARN


def test_a_5mm_pin_has_room_for_infill():
    shape = Box(20, 20, 4) + Pos(0, 0, 2) * Cylinder(3, 15, align=SEAT)
    assert only(shape, "pin") == []


def test_a_stub_has_nothing_to_lever_with():
    """The same 4mm diameter, under twice its height: a locating nub, not a pin."""
    shape = Box(20, 20, 4) + Pos(0, 0, 2) * Cylinder(2, 7, align=SEAT)
    assert only(shape, "pin") == []


def test_a_pin_lying_down_is_strands_not_rings():
    """Printed horizontal, bending loads continuous strands, not stacked welds."""
    shape = Box(4, 20, 20) + Pos(2, 0, 0) * Cylinder(1.25, 10, rotation=(0, 90, 0), align=SEAT)
    assert only(shape, "pin") == []


def test_a_bead_merged_into_a_wall_is_not_a_pin():
    """A half-round hugging a wall for its whole height loses part of its wrap to
    the join, and the wall carries the bending the rule worries about."""
    wall = Pos(0, 0, 2) * Box(2, 20, 10, align=SEAT)
    shape = Box(20, 20, 4) + wall + Pos(2, 0, 2) * Cylinder(1.25, 10, align=SEAT)
    assert only(shape, "pin") == []


def test_a_column_connected_at_both_ends_is_not_a_pin():
    """A narrow standoff between two plates has no free tip to lever at its base."""
    post = Pos(0, 0, 2) * Cylinder(2, 12, align=SEAT)
    cap = Pos(0, 0, 14) * Box(20, 20, 4)
    shape = Box(20, 20, 4) + post + cap
    assert len(shape.solids()) == 1
    assert only(shape, "pin") == []


def test_a_hole_is_the_same_surface_facing_inward():
    shape = Box(20, 20, 10) - Cylinder(1.25, 20)
    assert only(shape, "pin") == []


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
    """260 x 10 x 10 does not fit a 256 bed square-on, but it fits standing up."""
    tall = Box(260, 10, 10)
    assert only(tall, "build_volume", Context(bed=(256, 256, 300))) == [], "stands up"
    assert only(tall, "build_volume", Context(bed=(100, 100, 100)))[0].severity == FAIL


def test_build_volume_allows_a_diagonal_footprint():
    """The box is not the part: a 300mm bar lies on a 256mm bed at 30-odd degrees,
    and issue #55's 364mm tray sits on a 350mm bed the same way. Past the bed's
    diagonal, no rotation saves it."""
    bed = Context(bed=(256, 256, 100))  # too short to stand either bar on end
    assert only(Box(300, 10, 10), "build_volume", bed) == []
    assert only(Box(400, 10, 10), "build_volume", bed)[0].severity == FAIL


def test_build_volume_finds_a_narrow_rotation_window():
    """A long part can have less than 0.1 degrees of usable rotation."""
    angle = radians(36.05)
    bed = Context(
        bed=(
            300 * cos(angle) + 10 * sin(angle) + 0.1,
            300 * sin(angle) + 10 * cos(angle) + 0.1,
            100,
        )
    )
    assert only(Box(300, 10, 10), "build_volume", bed) == []


def test_build_volume_turns_a_stood_part_on_the_plate():
    """A stance fixes build-up, not rotation around build-up."""
    from nurb import stand

    stood = stand(Box(4, 120, 20), tilt=45, facet=2.0, fins=False)
    assert only(stood, "build_volume", Context(bed=(100, 100, 100))) == []


def test_build_volume_keeps_a_stood_parts_facet_on_the_bed():
    """Once stand() cuts the bed facet, the check may rotate only around build-up."""
    from nurb import stand

    stood = stand(Box(4, 30, 160), tilt=45, facet=2.0, fins=False)
    found = only(stood, "build_volume", Context(bed=(256, 256, 100)))
    assert len(found) == 1
    assert found[0].severity == FAIL


# --- bridges vs cantilevers --------------------------------------------------


def test_short_bridge_is_not_a_finding():
    """A slot through a block: its roof is 90deg, and every printer spans 10mm."""
    shape = Box(40, 40, 20) - Pos(0, 0, 6) * Box(10, 60, 6)
    assert only(shape, "overhang") == []


def test_long_bridge_warns_but_does_not_fail():
    shape = Box(80, 40, 20) - Pos(0, 0, 6) * Box(50, 60, 6)
    found = only(shape, "overhang")
    assert len(found) == 1
    assert found[0].severity == WARN
    assert found[0].value == pytest.approx(50, abs=0.1)


def test_bridge_limit_is_per_printer():
    shape = Box(40, 40, 20) - Pos(0, 0, 6) * Box(10, 60, 6)
    assert only(shape, "overhang", Context(bridge_limit=5)) != []
    assert only(shape, "overhang", Context(bridge_limit=30)) == []


def test_cantilever_still_fails_even_though_it_is_also_90_degrees():
    """The distinction the whole rule turns on: same angle, no support on one side."""
    shape = Box(6, 6, 20) + Pos(0, 0, 12) * Box(30, 30, 4)
    found = only(shape, "overhang")
    assert len(found) == 1
    assert found[0].severity == FAIL
    assert "unsupported" in found[0].message


# --- polish in the wrong place -----------------------------------------------


def test_bed_bevel_catches_a_chamfer_on_the_first_layer():
    from build123d import Axis, chamfer

    box = Box(20, 20, 20)
    bottom = chamfer(box.edges().group_by(Axis.Z)[0], 2)
    assert len(only(bottom, "bed_bevel")) == 4


def test_bed_bevel_catches_a_chamfer_beneath_a_narrow_wall():
    """A long, narrow bottom face is not enough to call a normally seated wall stood."""
    from build123d import Axis, chamfer

    wall = Box(4, 30, 20)
    bottom = chamfer(wall.edges().group_by(Axis.Z)[0], 1)
    assert len(only(bottom, "bed_bevel")) == 4


def test_bed_bevel_catches_a_circular_chamfer_on_the_first_layer():
    """The band is 1mm deep even though its plan-view bounding box is 20mm wide."""
    from build123d import chamfer

    cylinder = Cylinder(10, 20)
    bed = cylinder.bounding_box().min.Z
    bottom = [
        edge
        for edge in cylinder.edges()
        if abs(edge.bounding_box().min.Z - bed) < 1e-6
        and abs(edge.bounding_box().max.Z - bed) < 1e-6
    ]
    assert len(only(chamfer(bottom, 1), "bed_bevel")) == 1


def test_bed_bevel_ignores_a_chamfer_anywhere_else():
    from build123d import Axis, chamfer

    box = Box(20, 20, 20)
    assert only(chamfer(box.edges().group_by(Axis.Z)[-1], 2), "bed_bevel") == []


def test_bed_bevel_leaves_a_corbel_landing_on_the_plate_alone():
    """The doctrine's own 45 degree underside is not polish, however tilted it is.

    Rise is what separates them, and a bottom chamfer rises by its size exactly: 1, 2
    and 3mm, against 10mm for this corbel. Unlike plan-view reach, rise also works for a
    chamfer following a circular or diagonal edge.
    """
    body = Pos(0, 0, 10) * Box(20, 20, 20)  # standing on the plate at z=0
    wedge = Plane.XZ * Polygon((10, 0), (10, 10), (0, 0), align=None)
    post = body - extrude(wedge, 30, both=True)  # a 45 degree underside reaching 10mm
    assert only(post, "bed_bevel") == []
    # The same face against a part whose polish is 4mm, where 10mm of rise is back
    # inside chamfer territory. The rule is about scale, so it has to move with it.
    assert len(only(post, "bed_bevel", Context(cosmetic_chamfer=4.0))) == 1


def test_floating_ignores_a_vertex_resting_on_material_below():
    """The calipers-holder case, distilled: a corbel corner with every edge rising
    away from it, sitting directly on the body underneath. The edge test alone called
    it floating; the probe below is what clears it."""
    shape = Box(20, 20, 10) + Pos(0, 0, 10) * Box(12, 12, 10)
    assert only(shape, "floating") == []


def test_floating_catches_a_tip_hanging_in_air():
    """A leg tip whose faces all sit at 45 degrees: silent to the overhang rule,
    unprintable anyway, because its first layer has nothing to sit on."""
    from nurb import stand

    bracket = Pos(2, 15, 20) * Box(4, 30, 40) + Pos(17, 15, 38) * Box(26, 30, 4)
    found = only(stand(bracket, tilt=45, facet=2.0), "floating")
    assert found and all(f.severity == FAIL for f in found)


def test_floating_ignores_the_stairstep_corner_of_a_stood_slab():
    """The second-lowest corner of a tilted slab has air straight below it and prints
    fine: its silhouette descends to the facet, one layer resting on the next."""
    from nurb import stand

    assert only(stand(Box(4, 30, 40), tilt=45, facet=2.0), "floating") == []


def test_bed_bevel_leaves_a_standing_part_alone():
    """A 4mm wall stood at 45 rises 2.83mm off the plate, square in the chamfer band,
    and rise cannot tell it from a bevel. The stance can: the part has no bottom face
    whose rim a bevel could dress, only the facet it stands on."""
    from nurb import stand

    assert only(stand(Box(4, 30, 40), tilt=45, facet=2.0), "bed_bevel") == []


def test_concave_cosmetic_catches_polish_in_an_inside_corner():
    from build123d import chamfer

    shape = Box(20, 20, 20) - Pos(6, 0, 6) * Box(10, 30, 10)
    inner = [e for e in shape.edges()
             if abs(e.center().X - 1) < 1e-6 and abs(e.center().Z - 1) < 1e-6]
    assert len(inner) == 1
    assert len(only(chamfer(inner, 1), "concave_cosmetic")) == 1


def test_concave_cosmetic_leaves_a_deliberate_structural_chamfer_alone():
    """The 2mm relief the doctrine prescribes for thin material is not polish.

    Same corner, same rule, twice the chamfer. This fired six times at
    `mount_tape_measure` and again at `mount_akrobin_rail`, at the exact geometry the
    rule's own message tells you to use, because the limit was twice the strip a polish
    chamfer leaves rather than about equal to it. Both parts print.
    """
    from build123d import chamfer

    shape = Box(20, 20, 20) - Pos(6, 0, 6) * Box(10, 30, 10)
    inner = [e for e in shape.edges()
             if abs(e.center().X - 1) < 1e-6 and abs(e.center().Z - 1) < 1e-6]
    assert only(chamfer(inner, 2), "concave_cosmetic") == []


def test_concave_cosmetic_ignores_polish_on_an_outside_corner():
    from build123d import Axis, chamfer

    shape = chamfer(Box(20, 20, 20).edges().filter_by(Axis.Z), 1)
    assert only(shape, "concave_cosmetic") == []


def test_concave_cosmetic_does_not_mistake_a_pocket_for_a_chamfer():
    """A narrow pocket floor is bounded by concave edges too, and is square to them."""
    assert only(Box(20, 20, 20) - Pos(0, 0, 8) * Box(6, 6, 6), "concave_cosmetic") == []


# --- hole ceilings -----------------------------------------------------------


def counterbored_plate():
    """A 10mm plate with a naive counterbore, mouth on the bed: a 3.4mm hole over a
    6.2mm head pocket, the shelf between them laid flat over the open pocket."""
    plate = Box(30, 30, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    seated = (Align.CENTER, Align.CENTER, Align.MIN)
    return plate - Cylinder(1.7, 30, align=seated) - Cylinder(3.1, 3, align=seated)


def test_naive_counterbore_floats_its_hole_rim():
    """The overhang rule reads the shelf as a bridge and stays quiet on purpose; what
    it cannot see is the 3.4mm rim inside the bridge, drawn on air."""
    found = only(counterbored_plate(), "hole_ceiling")
    assert len(found) == 1
    assert found[0].severity == WARN
    assert found[0].value == pytest.approx(3.4, abs=0.05)
    assert only(counterbored_plate(), "overhang") == []


def test_stepped_counterbore_answers_the_finding():
    """The same pocket cut with counterbore() leaves nothing for any rule: every
    ceiling in the stack is a short bridge the existing rules already allow."""
    from nurb import counterbore

    plate = Box(30, 30, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    stepped = plate - counterbore(hole_dia=3.4, head_dia=6.2, head_depth=3, depth=12)
    assert len(stepped.solids()) == 1
    assert run(stepped) == []


def test_hole_through_a_bridged_roof_is_the_same_finding():
    """Not only screw pockets: a vertical hole meeting a channel roof from above puts
    its rim on the same sagging bridge lines."""
    shape = Box(40, 40, 20) - Pos(0, 0, 6) * Box(10, 60, 6) - Pos(0, 0, 15) * Cylinder(2, 14)
    found = only(shape, "hole_ceiling")
    assert len(found) == 1
    assert found[0].severity == WARN


def test_a_boss_through_a_ceiling_is_not_a_hole():
    """The inner wire alone cannot tell a hole from a column passing through the
    ceiling, and a column carries its own rim. The probe above settles it."""
    seated = (Align.CENTER, Align.CENTER, Align.MIN)
    shape = (
        Box(30, 30, 20, align=seated)
        - Box(20, 20, 10, align=seated)
        + Cylinder(2, 10, align=seated)
    )
    assert only(shape, "hole_ceiling") == []


def test_a_hollow_boss_through_a_ceiling_carries_its_rim():
    """A tube is still support even though probing its bounding-box centre finds
    the through hole rather than the wall that actually meets the ceiling."""
    seated = (Align.CENTER, Align.CENTER, Align.MIN)
    shape = (
        Cylinder(4, 20, align=seated)
        + Pos(0, 0, 10) * Cylinder(8, 3, align=seated)
        - Cylinder(2, 30, align=seated)
    )
    assert only(shape, "hole_ceiling") == []


def test_a_counterbore_mouth_on_the_bed_is_the_first_layer():
    """The plate's bottom face is pierced by the pocket too, and warning about the
    first layer is how a checker gets switched off."""
    found = only(counterbored_plate(), "hole_ceiling")
    assert all(f.where[2] > 0 for f in found)


# --- wall thickness ----------------------------------------------------------


@pytest.mark.parametrize("thickness,flagged", [(2.0, False), (1.5, False), (0.8, True), (0.4, True)])
def test_min_wall_measures_a_plain_plate(thickness, flagged):
    found = only(Box(30, 30, thickness), "min_wall")
    assert bool(found) is flagged
    if flagged:
        assert found[0].value == pytest.approx(thickness, abs=0.01)


def test_min_wall_measures_a_tube_wall():
    from build123d import Cylinder

    tube = Cylinder(10, 20) - Cylinder(9, 30)  # 1mm wall
    found = only(tube, "min_wall", Context(min_wall=1.5))
    assert found and found[0].value == pytest.approx(1.0, abs=0.05)


def test_min_wall_floor_is_per_part():
    plate = Box(30, 30, 1.0)
    assert only(plate, "min_wall", Context(min_wall=1.2)) != []
    assert only(plate, "min_wall", Context(min_wall=0.8)) == []


@pytest.mark.parametrize("allowed,flagged", [(9.5, True), (8.8, False)])
def test_min_wall_measures_a_skewed_section_with_a_sphere(allowed, flagged):
    """Through a skewed section the ray measures the slant, and the sphere corrects it.

    A wedge whose hypotenuse leans over the back face. The highest probe on the back
    sits 8mm from the hypotenuse plane, whose normal is 0.8 off the probe's axis, so
    the shortest chord any probe accepts is 10.0mm while the largest tangent sphere is
    2 * 8 / (1 + 0.8) = 8.89mm, both worked out by hand. A limit of 9.5 sits between
    them, which is exactly the case a ray cast alone gets wrong.
    """
    section = Plane.XZ * Polygon((0, 0), (30, 0), (0, 40), align=None)
    wedge = extrude(section, 10, both=True)
    found = only(wedge, "min_wall", Context(min_wall=allowed))
    assert bool(found) is flagged
    if flagged:
        assert found[0].value == pytest.approx(8.89, abs=0.05)


def test_min_wall_does_not_measure_across_a_chamfer_corner():
    """A ray that has already left the material must not count what it hits next.

    Without that filter a 1mm chamfer two corners away reads as a sub-millimetre wall
    on a part that is 20mm thick.
    """
    from build123d import Axis, chamfer

    shape = chamfer(Box(20, 20, 20).edges().filter_by(Axis.Z), 1)
    assert only(shape, "min_wall", Context(min_wall=2.0)) == []


def test_a_part_that_builds_nothing_still_tessellates():
    """The `solids` rule has words for an empty part, and the dev loop has to reach them.

    A part whose last cut removed everything tessellates to zero triangles, and asking
    trimesh for normals over that raises out of numpy. The rule's message never got
    seen: the viewer showed an IndexError from inside the mesher instead.
    """
    from nurb import builder

    empty = Box(10, 10, 10) - Box(20, 20, 20)
    assert only(empty, "solids")[0].value == 0
    assert len(builder.to_mesh(empty, 0.02).faces) == 0
    assert builder.to_glb(empty, 0.02), "an empty scene is still a GLB the viewer can load"


# --- what a finding is called on screen ----------------------------------------


def test_every_rule_has_a_label():
    """A rule with no label shows its identifier to somebody who owns a printer.

    This is the guard the site's "eight rules" headline needed and did not have: the
    moment a check ships without its plain-English name, this fails rather than the
    vocabulary leaking into the viewer.
    """
    from nurb.checks import LABELS, LABEL_WIDTH, RULES

    assert set(RULES) == set(LABELS), "every rule needs a label, and every label a rule"
    for rule, said in LABELS.items():
        assert said.islower(), f"{rule}: labels read as prose, not as headings"
        assert "_" not in said, f"{rule}: {said!r} is still an identifier"
        # The panel gives the label a fixed column; over this it wraps into two
        # ragged lines beside a message that is already wrapping.
        assert len(said) <= LABEL_WIDTH, f"{rule}: {said!r} will wrap in the panel"


def test_a_finding_carries_both_names():
    """The label is for whoever is looking; the rule is for whoever is fixing."""
    from nurb.checks import FAIL, Finding, label

    f = Finding("concave_cosmetic", FAIL, "x")
    assert f.label == "inside corner"
    assert f.rule == "concave_cosmetic", "the identifier never changes: the CLI prints it"
    assert "concave_cosmetic" in str(f), "and the CLI line still carries it"
    assert label("not_a_rule") == "not_a_rule", "an unlabelled rule shows itself, not nothing"


DOCTRINE_WORDS = (
    "polish", "facet", "concave", "gusset", "adhesion", "footprint", "center of mass",
    "bridging layers", "accounted for", "unsupported over", "b-rep", "chamfer band",
)


def user_facing_strings():
    """Every label, and the literal text of every `plain=` a rule passes.

    Read out of the source rather than provoked out of geometry: a fixture-driven
    version only covers the rules whose shape somebody remembered to build, and the
    rules most likely to speak the doctrine are the fiddly ones nobody fixtures.
    """
    import ast
    import pathlib

    from nurb import checks

    said = [(rule, text) for rule, text in checks.LABELS.items()]
    source = pathlib.Path(checks.__file__).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg != "plain":
                continue
            parts = kw.value.values if isinstance(kw.value, ast.JoinedStr) else [kw.value]
            literal = " ".join(
                p.value for p in parts if isinstance(p, ast.Constant) and isinstance(p.value, str)
            )
            said.append((f"line {node.lineno}", literal))
    return said


def test_nothing_a_person_reads_speaks_the_doctrine():
    """The label and the plain sentence are the whole user-facing surface. Neither may
    use a word that only means something to whoever wrote the rule."""
    said = user_facing_strings()
    assert len(said) > len(__import__("nurb").checks.LABELS), "no plain= strings were found"
    for where, text in said:
        for word in DOCTRINE_WORDS:
            assert word not in text.lower(), f"{where}: user-facing text says {word!r}"


def test_the_agent_still_gets_the_exact_sentence():
    """The plain twin is additive: the CLI line and `message` never soften."""
    from nurb.checks import Context, run

    shape = Box(30, 30, 0.5)
    found = [f for f in run(shape, Context()) if f.rule == "min_wall"]
    assert found and "lays down reliably" in found[0].message


def test_a_message_that_is_already_plain_needs_no_twin():
    """`plain` is None where the message is fine, and `said` falls through to it."""
    from nurb.checks import FAIL, Finding

    f = Finding("floating", FAIL, "a region's first layer sits on air")
    assert f.plain is None
    assert f.said == f.message


# --- supports ----------------------------------------------------------------


def _slotted(span=44.0, height=40.0):
    """A slot the printer cannot bridge: one overhang finding, nothing else."""
    return Box(90, 20, height) - Pos(0, 0, -height / 2 + 10) * Box(span, 20, 16)


def test_the_card_flag_turns_an_overhang_into_a_note():
    plain = only(_slotted(), "overhang")
    assert [f.severity for f in plain] == [WARN]
    carried = only(_slotted(), "overhang", Context(supports=True))
    assert [f.severity for f in carried] == [NOTE]
    # The angle and the area survive: the point of keeping the finding is that the
    # user can still see the size of what the supports are carrying.
    assert carried[0].value == plain[0].value


def test_a_cantilever_fails_until_it_is_carried():
    post = Box(10, 10, 40)
    shape = post + Pos(12, 0, 15) * Box(24, 10, 3)
    assert [f.severity for f in only(shape, "overhang")] == [FAIL]
    assert [f.severity for f in only(shape, "overhang", Context(supports=True))] == [NOTE]


def test_a_mark_carries_its_own_feature_and_nothing_else():
    """The whole reason to mark a feature rather than declare the part: an identical
    overhang somewhere else in the same body still fails."""
    body = Box(120, 20, 40)
    with supports.collecting() as marked:
        left = supports.supported(
            Pos(-32, 0, -10) * Box(44, 20, 16), "the bundle sets this span"
        )
        right = Pos(32, 0, -10) * Box(44, 20, 16)
        shape = body - left - right
    shape._nurb_supported = tuple(marked)

    found = only(shape, "overhang")
    by_severity = {f.severity: f for f in found}
    assert set(by_severity) == {NOTE, WARN}
    assert by_severity[NOTE].where[0] < 0 < by_severity[WARN].where[0]
    assert "the bundle sets this span" in by_severity[NOTE].message


def test_a_mark_that_carries_nothing_says_so():
    """Either the geometry got fixed and the mark outlived it, or the mark stopped
    landing where it used to. Both are worth a word; neither is a failure."""
    with supports.collecting() as marked:
        supports.supported(Box(10, 10, 10), "left over from the slot that was here")
        shape = Box(60, 20, 40)
    shape._nurb_supported = tuple(marked)

    found = only(shape, "overhang")
    assert [f.severity for f in found] == [NOTE]
    assert "nothing here needed supports" in found[0].message
    assert found[0].value is None  # what tells it apart from a finding being carried


def test_supports_never_excuse_what_geometry_has_to_answer():
    """floating, hole_ceiling and stability each have a doctrine answer that is not
    support material, so neither declaration touches them."""
    post = Box(10, 10, 40)
    hanging = post + Pos(12, 0, 15) * Box(24, 10, 3)
    for rule in ("floating", "stability", "hole_ceiling"):
        plain = only(hanging, rule)
        carried = only(hanging, rule, Context(supports=True))
        assert [f.severity for f in plain] == [f.severity for f in carried]
    assert only(hanging, "floating")  # and the case above really does fire one


def test_a_mark_survives_the_transform_that_stands_a_part():
    """`stand()` moves the whole part after the mark was made, so it moves the mark
    too. Without that the mark describes where the feature used to be."""
    with supports.collecting() as marked:
        body = Box(30, 20, 60)
        supports.supported(body, "the mounting face has to stay flat")
        shape = stand(body, 60, fins=False)
    shape._nurb_supported = tuple(marked)

    assert [f.severity for f in only(shape, "overhang")] == [NOTE]
