"""Hook - Scissors - 1x. Read hook_scissors.md before changing anything."""

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


@part
def hook_scissors(
    bracket_count=1,
    item_height=30.0,
    item_depth=6.0,
    hook_projection=28.0,
    hook_width=15.0,
    arm_thickness=6.0,
    upstand_height=15.0,
    upstand_thickness=6.0,
    chamfer_size=1.0,
    structural_chamfer=3.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"arm would not reach the slab. Raise it above {MIN_ITEM_DEPTH}."
        )

    # The strip of slab left standing beside the arm carries the polish on the slab's own
    # front corner, so it has to be wider than that chamfer. Measured here: builds at
    # 1.08mm and fails at 1.00mm, and flush (no strip at all) is fine again.
    margin = (bracket_count * BLOCK_WIDTH - hook_width) / 2
    if 0 < margin <= chamfer_size:
        raise ValueError(
            f"a {hook_width}mm cradle leaves a {margin:.2f}mm strip of slab either side, too "
            f"narrow to carry the {chamfer_size}mm polish on its own corner. Narrow the cradle "
            f"below {bracket_count * BLOCK_WIDTH - 2 * chamfer_size:.2f}, run it flush at "
            f"{bracket_count * BLOCK_WIDTH:.2f}, or add a bracket."
        )

    back = slab(bracket_count, item_height, item_depth)

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
    #
    # Across the weld, not around it. The two vertical legs where the arm's sides meet
    # the slab carry almost none of the moment, and relieving them eats the strip of
    # slab beside the arm: at a 20mm cradle that strip is 2.58mm and a 3mm band cannot
    # land on it at all. Chamfering the weld alone is what lets the wide-cradle utility
    # hooks exist on one bracket.
    weld = new_edges(back, arm, combined=body).filter_by(Axis.Y).filter_by(
        lambda e: e.center().Z > floor + EPS
    )
    corner = body.edges().filter_by(Axis.Y).filter_by(
        lambda e: abs(e.center().X - inner) < EPS and abs(e.center().Z - arm_top) < EPS
    )
    body = chamfer(list(weld) + list(corner), structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm: everything exposed except the structural chamfers we just made
    # and the faces they landed on, which are concave and would sliver.
    polish = polish_edges(body, item_height) - new_edges(pristine, combined=body)
    return chamfer(polish, chamfer_size)
