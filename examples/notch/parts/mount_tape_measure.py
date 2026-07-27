"""Mount - Tape Measure - 2x. Read mount_tape_measure.md before changing anything."""

from nurb import *

from system import (
    BLOCK_WIDTH,
    EPS,
    MIN_ITEM_DEPTH,
    MIN_ITEM_HEIGHT,
    OVERSHOOT,
    channels,
    detent_dimples,
    polish as polish_pass,
    polish_edges,
    span,
)


@part
def mount_tape_measure(
    bracket_count=2,
    item_height=28.0,
    item_depth=6.0,
    band_wall=2.0,
    band_reach=8.0,
    chamfer_size=1.0,
    structural_chamfer=2.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material between the channel floor and the "
            f"back of the slot, so the detent dimple would break through into it. Raise it "
            f"above {MIN_ITEM_DEPTH}."
        )

    if item_height < MIN_ITEM_HEIGHT:
        raise ValueError(
            f"item_height {item_height} is below the {MIN_ITEM_HEIGHT}mm a bracket needs for "
            f"full engagement, and the band runs the whole slab height, so a short slab is a "
            f"short band as well. Raise it to {MIN_ITEM_HEIGHT} or more."
        )

    # The slot's side faces are `band_reach - band_wall` long and carry a structural
    # chamfer at each end. Two chamfers need strictly more than twice their size of face
    # between them, and this part sits one hundredth of a millimetre off that line:
    # measured here, a 6.00mm slot fails at 3mm and a 6.01mm slot builds. That is the
    # whole reason `structural_chamfer` is 2mm rather than the family's 3mm.
    slot_depth = band_reach - band_wall
    if 2 * structural_chamfer >= slot_depth:
        raise ValueError(
            f"a {structural_chamfer}mm chamfer at each end of a {slot_depth}mm slot side "
            f"leaves the kernel no face to land on. Drop structural_chamfer below "
            f"{slot_depth / 2}, or raise band_reach above {band_wall + 2 * structural_chamfer}."
        )

    slab_width = bracket_count * BLOCK_WIDTH
    opening = slab_width - 2 * band_wall
    mid = span(bracket_count)

    # Slab and band are flush in y and z, so together they are one plain block and the
    # slot is what makes them a band. Fusion built BandOuter and Band as separate
    # features because it had to; here two boxes that meet on a face would only risk
    # fusing to two solids.
    depth = item_depth + band_reach
    body = Pos(-depth / 2, mid, -item_height / 2) * Box(depth, slab_width, item_height)

    # The slot, vertical and open top and bottom, which is what makes the part print
    # bottom-down with no support. The overshoot keeps its end faces off the block's,
    # since coincident faces make brittle booleans.
    slot_front = -depth + band_wall
    slot_back = -item_depth
    slot = Pos((slot_front + slot_back) / 2, mid, -item_height / 2) * Box(
        slot_back - slot_front, opening, item_height + 2 * OVERSHOOT
    )

    body = (
        body
        - slot
        - channels(bracket_count, item_height)
        - detent_dimples(bracket_count)
    )

    # Structural, 2mm: the four inside corners of the slot, back pair against the slab
    # and front pair against the rail. Selected by coordinate rather than `new_edges`
    # because the slot is a cut and there is no fuse to report on, and because nothing
    # has moved the topology yet: this is the first chamfer on the part. Both
    # coordinates are derived from the parameters, so they track `bracket_count`.
    corners = body.edges().filter_by(Axis.Z).filter_by(
        lambda e: (
            (abs(e.center().X - slot_back) < EPS or abs(e.center().X - slot_front) < EPS)
            and abs(abs(e.center().Y - mid) - opening / 2) < EPS
        )
    )
    body = chamfer(corners, structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm, on the outside only. The whole slot rim stays sharp: the back and
    # side segments share vertices with the 2mm structural corners, and the front
    # segment is 2mm from the block's own front edge, which is exactly twice the
    # chamfer and one hundredth short of what the kernel needs. See the card.
    def slot_rim(edge):
        bb = edge.bounding_box()
        return (
            bb.min.Z > -EPS
            and bb.min.X > slot_front - EPS
            and bb.max.X < slot_back + EPS
        )

    polish = polish_edges(body, item_height).filter_by(lambda e: not slot_rim(e))
    return polish_pass(body, polish, chamfer_size)
