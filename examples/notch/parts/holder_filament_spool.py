"""Holder - Filament Spool - 2x. Read holder_filament_spool.md before changing anything."""

from nurb import *

from system import (
    BLOCK_WIDTH,
    CHANNEL_DEPTH,
    EPS,
    FLOOR_X,
    polish as polish_pass,
    polish_edges,
    slab,
    span,
)

# The ramp stops this far below the slab top. It keeps the slab-top front edge one
# clean full-width chamfered edge instead of three pieces, and it holds the arm-root
# structural chamfers clear of that edge's own polish band.
RAMP_GAP = 3.0


@part
def holder_filament_spool(
    bracket_count=2,
    item_height=65.0,
    item_depth=6.0,
    arm_width=22.0,
    arm_height=36.0,
    usable_length=120.0,
    nose_height=10.0,
    nose_thickness=8.0,
    arm_overlap=1.0,
    chamfer_size=1.0,
    structural_chamfer=3.0,
    draft=False,
):
    # The bar's y-band overlaps both channel dovetails, so how far it reaches back is
    # the whole fit question. Short of the slab front face it only touches and fuses to
    # two loose solids; past the channel floor it fills the dovetails and the part will
    # not go on the wall.
    if not 0 < arm_overlap < item_depth - CHANNEL_DEPTH:
        raise ValueError(
            f"arm_overlap {arm_overlap} has to land the arm's back face between the slab "
            f"front at x={-item_depth:g} and the channel floor at x={FLOOR_X:g}, so it must "
            f"be above 0 and below {item_depth - CHANNEL_DEPTH:g}. 1.0 is the shipped value."
        )

    # The slab has to stand wide enough beside the bar to carry a 3mm relief band and
    # still leave face for its own corner polish. Measured on this part: builds at a
    # 4.08mm strip and fails at 4.00mm, which is structural_chamfer + chamfer_size.
    strip = (bracket_count * BLOCK_WIDTH - arm_width) / 2
    if 0 < strip <= structural_chamfer + chamfer_size:
        raise ValueError(
            f"a {arm_width:g}mm bar on {bracket_count} bracket(s) leaves a {strip:.2f}mm strip "
            f"of slab either side, too narrow for the {structural_chamfer:g}mm arm-root relief "
            f"plus the {chamfer_size:g}mm polish on the slab's own corner. Add a bracket, or "
            f"narrow the bar below "
            f"{bracket_count * BLOCK_WIDTH - 2 * (structural_chamfer + chamfer_size):.2f}."
        )

    # Derived in Fusion as expressions rather than parameters, and they stay expressions
    # here. The ramp's rise is item_height - arm_height - RAMP_GAP and its run is the
    # same number, so the gusset is 45 degrees by construction and not by dimension.
    ramp_run = item_height - arm_height - RAMP_GAP
    arm_length = ramp_run + usable_length + nose_thickness

    back = slab(bracket_count, item_height, item_depth)

    floor = -item_height
    arm_top = floor + arm_height
    root = -(item_depth - arm_overlap)
    ramp_base = -(item_depth + ramp_run)
    nose_back = -(item_depth + ramp_run + usable_length)
    tip = -(item_depth + arm_length)

    # Ramp, ride zone and nose in one side profile. The bar's bottom runs at bed level
    # the whole way, so nothing here needs support, and drawing it as one polygon keeps
    # the three of them one solid with interior junctions.
    section = Plane.XZ * Polygon(
        (root, floor),
        (tip, floor),
        (tip, arm_top + nose_height),
        (nose_back, arm_top + nose_height),
        (nose_back, arm_top),
        (ramp_base, arm_top),
        (-item_depth, -RAMP_GAP),
        (root, -RAMP_GAP),
        align=None,
    )
    blank = extrude(section, arm_width / 2, both=True)

    # The crest. A radius of exactly half the width on both top edges at once is what
    # makes a true half-cylinder, and OCCT will not do it: 11.0 fails and so does
    # 10.999999, the largest that builds being 10.999995. Every radius that does build
    # leaves a land along the top, which is either a sliver or a visible flat.
    #
    # One edge at a time is fine, because r is then half the face and not all of it. So
    # round each top edge on its own copy of the blank and intersect the two: each copy
    # carries one quarter round, the intersection carries both, and they meet tangent at
    # the top with no land at all. Each also keeps the runout where its fillet dies into
    # the ramp, which a cutting tool sized to the ride zone would not.
    tops = blank.edges().filter_by(Axis.X).filter_by(
        lambda e: abs(e.center().Z - arm_top) < EPS
    ).group_by(Axis.Y)
    rounded = fillet(tops[0], arm_width / 2) & fillet(tops[-1], arm_width / 2)
    arm = Pos(0, span(bracket_count), 0) * rounded

    body = back + arm
    pristine = body

    # Structural, 3mm: the arm root, which is where 3.3 N.m of spool comes into the
    # wall. `new_edges` returns the two vertical legs of the weld and nothing else,
    # because the ramp-to-slab edge along the top already existed on the arm.
    #
    # That edge stays sharp, and the RAMP_GAP is why: a 3mm band on it would run the
    # full 3mm up the slab front face and land exactly on the slab top.
    body = chamfer(new_edges(back, arm, combined=body), structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm, with two exclusions beyond the standing vetoes.
    #
    # The crest's two tangent lines, where the half-cylinder meets the flat sides, are
    # neither convex nor concave, and `is_convex` splits on them: one comes back concave
    # and the other convex, so half of a symmetric part would get chamfered. A chamfer
    # there would cut a flat into the surface the spool bore rides on regardless.
    #
    # The two sloped ramp flanks share their top vertex with the arm-root relief, so a
    # 1mm band and a 3mm band would have to meet there. Left sharp, and found by the one
    # thing that distinguishes them: everything else here is axis aligned, so they are
    # the only candidates that run in x and z at once. The test also picks up the two
    # short sloped edges capping the relief bands, which `new_edges` drops below anyway.
    tangent = arm_top - arm_width / 2

    def excluded(edge):
        bb = edge.bounding_box()
        if abs(bb.min.Z - tangent) < EPS and abs(bb.max.Z - tangent) < EPS:
            return True
        return bb.max.X - bb.min.X > EPS and bb.max.Z - bb.min.Z > EPS

    polish = polish_edges(body, item_height).filter_by(lambda e: not excluded(e))
    return polish_pass(body, polish - new_edges(pristine, combined=body), chamfer_size)
