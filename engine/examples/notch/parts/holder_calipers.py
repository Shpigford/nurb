"""Holder - Calipers - 2x. Read holder_calipers.md before changing anything."""

from math import floor as _floor

from nurb import *

from system import (
    BLOCK_WIDTH,
    EPS,
    MERGE_X,
    MIN_ITEM_DEPTH,
    polish_edges,
    slab,
    span,
)


def _post_section(front, lip_back, saddle, bed, corbel_tip):
    """One saddle post drawn in section: floor, lip, and the corbel under both.

    The underside is a corbel at exactly 45 degrees, which is a short vertical tip of
    `corbel_tip` below the floor at the front face and then a plane falling back into
    the body. Where that plane lands is not a choice. With room to fall it reaches the
    bed and leaves a footprint; without, it roots partway up the slab front. The two
    posts here sit at different heights and take one form each, and the switch is
    arithmetic rather than a parameter.
    """
    tip = saddle - corbel_tip
    rise, run = tip - bed, MERGE_X - front
    if rise <= run:
        underside = [(front + rise, bed), (MERGE_X, bed)]
    else:
        underside = [(MERGE_X, tip - run)]
    return Polygon(
        (front, 0.0),  # the lip tops out flush with the slab, never above it
        (front, tip),
        *underside,
        (MERGE_X, saddle),
        (lip_back, saddle),
        (lip_back, 0.0),
        align=None,
    )


@part
def holder_calipers(
    bracket_count=2,
    item_height=30.0,
    item_depth=6.0,
    cradle_depth=14.0,
    saddle_height=24.0,
    roller_relief=15.0,
    lip_thickness=4.0,
    beam_slot=35.0,
    corbel_tip=4.0,
    chamfer_size=1.0,
    structural_chamfer=3.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"saddle posts would not reach the slab. Raise it above {MIN_ITEM_DEPTH}."
        )

    width = bracket_count * BLOCK_WIDTH
    post = (width - beam_slot) / 2
    if post <= 2 * chamfer_size:
        need = _floor((beam_slot + 4 * chamfer_size) / BLOCK_WIDTH) + 1
        raise ValueError(
            f"a {beam_slot:g}mm beam slot across a {width:.2f}mm slab leaves nothing to "
            f"stand the saddles on: each post comes out {post:.2f}mm wide and it has to "
            f"clear twice the {chamfer_size:g}mm polish to carry a chamfer on both front "
            f"corners. Drop beam_slot below {width - 4 * chamfer_size:.2f}, or raise "
            f"bracket_count to {need}."
        )

    if saddle_height >= item_height:
        raise ValueError(
            f"saddle_height {saddle_height} reaches the {item_height}mm slab top, so there "
            f"is no lip left to hold the caliper in. Keep it under {item_height}."
        )

    if roller_relief >= saddle_height - corbel_tip:
        raise ValueError(
            f"roller_relief {roller_relief} drops the +y saddle to "
            f"{saddle_height - roller_relief:.1f}mm above the bed, which is under the "
            f"{corbel_tip}mm corbel tip that hangs below it. Keep it under "
            f"{saddle_height - corbel_tip:g}, or lower corbel_tip."
        )

    back = slab(bracket_count, item_height, item_depth)

    bed = -item_height
    front = -(item_depth + cradle_depth)  # the front face of the lip
    lip_back = front + lip_thickness  # and the back of the head pocket
    high = bed + saddle_height
    low = high - roller_relief

    # The saddles are deliberately uneven. The caliper's housing has a straight bottom
    # edge, but the thumb roller hangs `roller_relief` below it on one side and there is
    # no clean edge outboard of the roller to relieve around, so a level cradle sits
    # crooked. The -y post catches the clean edge high and the +y post catches the roller
    # low, and the two land the caliper level. Swapping them hangs it crooked by design.
    mid = span(bracket_count)
    reach = (beam_slot + post) / 2
    posts = Part() + [
        Pos(0, mid + side * reach, 0)
        * extrude(
            Plane.XZ * _post_section(front, lip_back, saddle, bed, corbel_tip),
            post / 2,
            both=True,
        )
        for side, saddle in ((-1, high), (1, low))
    ]

    body = back + posts
    pristine = body

    # Structural, 3mm, at the four junctions the caliper's weight runs through: each
    # saddle floor where it lands on the slab front, and where it meets its own lip.
    # Both floor levels, since both carry load.
    def at_floor(edge):
        return any(abs(edge.center().Z - z) < EPS for z in (high, low))

    weld = new_edges(back, posts, combined=body).filter_by(Axis.Y).filter_by(at_floor)
    root = body.edges().filter_by(Axis.Y).filter_by(
        lambda e: abs(e.center().X - lip_back) < EPS and at_floor(e)
    )
    body = chamfer(list(weld) + list(root), structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm, with three exclusions on top of the standing ones. The structural
    # bands themselves, and any edge running into one of their corners: a 1mm facet
    # landing on the end of a 3mm band is a compound corner the kernel has to blend, and
    # leaving those ten edges sharp is what keeps the polish pass from depending on it.
    # It also takes the sliver count from ten to four.
    made = new_edges(pristine, combined=body)
    corners = [tuple(v) for e in made for v in e.vertices()]

    def blends(edge):
        return any(
            all(abs(a - b) < EPS for a, b in zip(tuple(v), c))
            for v in edge.vertices()
            for c in corners
        )

    # And the third exclusion, which `polish_edges` does not cover: a sloped edge that
    # runs down to the build plate. It vetoes an edge lying in the bottom face, and a
    # vertical corner that merely ends there is fine because its chamfer stands square to
    # the plate. The low post's corbel sides arrive at 45 degrees, so their chamfers land
    # tilted and lay a knife edge into the first layer. `nurb check` catches it as
    # `bed_bevel`, which is the rule doing its job.
    # A sloped edge reaching the bed used to need excluding here too, and now it does
    # not: `polish_edges` vetoes it, which is where the rest of the bottom-face rule
    # already lived.
    #
    # The saddle floors do, and they are the one exclusion on this part that is fit
    # rather than kernel. A ~40mm housing lands about 2.5mm of edge on a 7.66mm post,
    # so a millimetre off each side of that floor is a quarter of the bearing surface
    # on a part that is already marginal there. Mating geometry, and the doctrine's
    # veto covers it.
    def bearing(edge):
        bb = edge.bounding_box()
        return any(
            abs(bb.min.Z - floor) < EPS and abs(bb.max.Z - floor) < EPS
            for floor in (bed + saddle_height, bed + saddle_height - roller_relief)
        )

    wanted = (polish_edges(body, item_height) - made).filter_by(lambda e: not bearing(e))
    return polish(body, wanted, chamfer_size)
