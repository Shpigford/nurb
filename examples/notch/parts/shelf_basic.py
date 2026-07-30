"""Shelf - Basic - 4x. Read shelf_basic.md before changing anything."""

from nurb import *

from system import (
    EPS,
    MERGE_X,
    MIN_ITEM_DEPTH,
    plate_width,
    polish_edges,
    slab,
    span,
)


@part
def shelf_basic(
    bracket_count=4,
    item_height=45.0,
    item_depth=6.0,
    shelf_depth=100.0,
    shelf_thickness=6.0,
    lip_height=5.0,
    lip_thickness=3.0,
    gusset_thickness=3.0,
    gusset_tip=6.0,
    gusset_drop=3.0,
    chamfer_size=1.0,
    structural_chamfer=3.0,
    draft=False,
):
    """A flat shelf on a hanging plate, with a lip and two triangular gussets.

    bracket_count: how many brackets the shelf spans
    item_height: how tall the plate on the wall is
    item_depth: how thick the plate is, wall to front face
    shelf_depth: how far the platform sticks out from the plate
    shelf_thickness: how thick the platform is
    lip_height: how far the front lip rises above the platform
    lip_thickness: how thick the front lip is
    gusset_thickness: how thick each triangular support fin is
    gusset_tip: how much of each gusset's sharp outer corner is cut off
    gusset_drop: how far below the plate's top edge the gussets peak
    chamfer_size: size of the cosmetic chamfer on exposed edges
    structural_chamfer: size of the load chamfer where the platform meets the plate
    """
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"platform would not reach the slab. Raise it above {MIN_ITEM_DEPTH}."
        )

    # Two polished convex edges need strictly more than `2 * chamfer_size` of face
    # between them. This part sits one notch from that rule in two places, and both
    # fail with the bare OCCT message rather than anything that names the cause.
    # Measured here: the threshold is exactly 2 * chamfer_size at 0.5, 0.8, 1.0 and 1.25.
    if gusset_drop <= 2 * chamfer_size:
        raise ValueError(
            f"gusset_drop {gusset_drop} leaves the gusset peak inside the slab top's "
            f"{chamfer_size}mm polish band, and OCCT cannot build the corner. Raise it "
            f"above {2 * chamfer_size}, or drop chamfer_size below {gusset_drop / 2}."
        )
    if lip_thickness <= 2 * chamfer_size:
        raise ValueError(
            f"a {lip_thickness}mm lip cannot carry a {chamfer_size}mm polish on both of "
            f"its top edges. Raise lip_thickness above {2 * chamfer_size}, or drop "
            f"chamfer_size below {lip_thickness / 2}."
        )

    # The gusset is a true 45: its run and its rise are both `gusset_depth`. Both acute
    # tips of that triangle get cut off, and what is left has to be worth drawing.
    gusset_depth = item_height - shelf_thickness
    if gusset_depth <= gusset_tip + gusset_drop:
        raise ValueError(
            f"a {gusset_depth}mm gusset is all tip: {gusset_tip}mm truncation plus "
            f"{gusset_drop}mm drop leaves nothing sloping. Raise item_height above "
            f"{shelf_thickness + gusset_tip + gusset_drop}, or cut gusset_tip."
        )

    width = plate_width(bracket_count)
    back = slab(bracket_count, item_height, item_depth)

    # Everything forward hangs off the bracket run's midpoint, not off y=0.
    mid = span(bracket_count)
    top = -item_height + shelf_thickness  # the platform's top face
    front = -(item_depth + shelf_depth)

    # The platform sits at the bottom of the slab, so its underside is the bed and the
    # whole shelf prints flat and support-free.
    platform = Pos((MERGE_X + front) / 2, mid, top - shelf_thickness / 2) * Box(
        MERGE_X - front, width, shelf_thickness
    )
    lip = Pos(front + lip_thickness / 2, mid, top + lip_height / 2) * Box(
        lip_thickness, width, lip_height
    )

    # Gussets at the outer ends, flush with the platform sides. The profile is a 45
    # degree triangle with both sharp corners cut off: `gusset_tip` at the outer end,
    # `gusset_drop` at the peak.
    peak = -gusset_drop
    tip_x = -item_depth - (gusset_depth - gusset_drop - gusset_tip)
    section = Plane.XZ * Polygon(
        (MERGE_X, top),
        (tip_x, top),
        (tip_x, top + gusset_tip),
        (-item_depth, peak),
        (MERGE_X, peak),
        align=None,
    )
    fin = extrude(section, gusset_thickness / 2, both=True)
    reach = (width - gusset_thickness) / 2
    fins = Part() + [Pos(0, mid + s * reach, 0) * fin for s in (-1, 1)]

    shelf = platform + lip + fins
    body = back + shelf
    pristine = body

    # Structural, 3mm: the platform-to-slab load junction, and only that. The gusset
    # roots are concave too, but a gusset is 3mm thick and a 3mm chamfer would eat it.
    junction = [
        e
        for e in new_edges(back, shelf, combined=body)
        if abs(e.bounding_box().min.Z - top) < EPS and abs(e.bounding_box().max.Z - top) < EPS
    ]
    body = chamfer(junction, structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm. On top of the standing vetoes: nothing bounding a gusset's slope or
    # its tip face. Both are thin-web edges, where a chamfer leaves a runout sliver
    # rather than taking a corner off.
    slope = peak + item_depth  # z - x, constant along the 45 degree face
    bands = [
        (mid + s * reach - gusset_thickness / 2, mid + s * reach + gusset_thickness / 2)
        for s in (-1, 1)
    ]

    def on_gusset(edge):
        here = edge.center()
        if here.X < tip_x - EPS or here.X > -item_depth + EPS:
            return False
        if not any(lo - EPS <= here.Y <= hi + EPS for lo, hi in bands):
            return False
        return abs(here.Z - here.X - slope) < EPS or abs(here.X - tip_x) < EPS

    wanted = polish_edges(body, item_height).filter_by(lambda e: not on_gusset(e))
    return polish(body, wanted - new_edges(pristine, combined=body), chamfer_size)
