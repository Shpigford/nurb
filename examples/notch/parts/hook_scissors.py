"""Hook - Scissors - 1x. Read hook_scissors.md before changing anything."""

from nurb import *

from system import (
    BLOCK_WIDTH,
    EPS,
    MERGE_X,
    MIN_ITEM_DEPTH,
    channels,
    detent_dimples,
    polish_edges,
    span,
)


@part
def hook_scissors(
    bracket_count=1,
    item_height=30,
    item_depth=6,
    hook_projection=28,
    hook_width=15,
    arm_thickness=6,
    upstand_height=15,
    upstand_thickness=6,
    chamfer_size=1.0,
    structural_chamfer=3.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"arm would not reach the slab. Raise it above {MIN_ITEM_DEPTH}."
        )

    y0, y1 = -BLOCK_WIDTH / 2, (bracket_count - 0.5) * BLOCK_WIDTH
    slab = Pos(-item_depth / 2, (y0 + y1) / 2, -item_height / 2) * Box(
        item_depth, y1 - y0, item_height
    )
    back = slab - channels(bracket_count, item_height) - detent_dimples(bracket_count)

    # The J, drawn once in section and swept across. Bottom-weighted: the arm and
    # its upstand sit on the floor of the slab, so the load hangs under the stop.
    floor = -item_height
    arm_top = floor + arm_thickness
    tip = -(item_depth + hook_projection)
    inner = tip + upstand_thickness
    crest = arm_top + upstand_height
    section = Plane.XZ * Polygon(
        (MERGE_X, floor),
        (tip, floor),
        (tip, crest),
        (inner, crest),
        (inner, arm_top),
        (MERGE_X, arm_top),
        align=None,
    )
    arm = Pos(0, span(bracket_count), 0) * extrude(section, hook_width / 2, both=True)

    body = arm + back
    pristine = body

    # Structural, 3mm: the two concave junctions the load runs through. `new_edges`
    # gives the arm-to-slab weld exactly, which no geometric selector does once a
    # chamfer has already moved the topology around.
    junction = [e for e in new_edges(back, arm, combined=body) if e.center().Z > floor + EPS]
    corner = body.edges().filter_by(Axis.Y).filter_by(
        lambda e: abs(e.center().X - inner) < EPS and abs(e.center().Z - arm_top) < EPS
    )
    body = chamfer(junction + list(corner), structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm: everything exposed except the structural chamfers we just made
    # and the faces they landed on, which are concave and would sliver.
    polish = polish_edges(body, item_height) - new_edges(pristine, combined=body)
    return chamfer(polish, chamfer_size)
