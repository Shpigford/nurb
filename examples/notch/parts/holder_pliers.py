"""Holder - Pliers - 6x. Read holder_pliers.md before changing anything."""

from math import ceil

from nurb import *

from system import (
    BLOCK_WIDTH,
    FLOOR_X,
    MERGE_X,
    MIN_ITEM_DEPTH,
    OVERSHOOT,
    plate_width,
    polish,
    polish_edges,
    slab,
    span,
)

# Material left between the back of a pocket and the channel floor. 2.8mm at the
# defaults, and it is the whole reason the pockets stop at x=-7 rather than running
# back to the slab: any less and the dovetail has nothing behind it.
MIN_WEB = 2.0

# Solid slab either side of the pocket run. Below this the end wall is thinner than the
# doctrine's minimum and the polish on the slab's own corner has nowhere to land.
MIN_END_WALL = 3.0


@part
def holder_pliers(
    bracket_count=6,
    item_height=30.0,
    item_depth=6.0,
    block_depth=30.0,
    wall_height=15.0,
    pocket_count=5,
    pocket_size=20.0,
    pocket_pitch=30.0,
    front_wall=3.0,
    chamfer_size=1.0,
    structural_chamfer=3.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"block would not reach the slab. Raise it above {MIN_ITEM_DEPTH}."
        )

    # Pockets are dimensioned from the front face back, because `front_wall` is the
    # number that has to hold and the web behind them is what is left over.
    pocket_front = -(block_depth - front_wall)
    pocket_back = pocket_front + pocket_size
    web = FLOOR_X - pocket_back
    if web < MIN_WEB:
        raise ValueError(
            f"a {pocket_size}mm pocket behind a {front_wall}mm front wall on a "
            f"{block_depth}mm block leaves {web:.2f}mm of web in front of the channel "
            f"floor, under the {MIN_WEB}mm minimum. Deepen "
            f"block_depth to {front_wall + pocket_size - FLOOR_X + MIN_WEB:.1f} or shorten "
            f"the pocket to {block_depth - front_wall + FLOOR_X - MIN_WEB:.1f}."
        )

    # The pocket run has to land on the plate with a wall at each end. This is the
    # constraint that decides bracket_count on this part: pitch buys head clearance and
    # the plate only comes in 25.16mm steps.
    run = (pocket_count - 1) * pocket_pitch + pocket_size
    end_wall = (bracket_count * BLOCK_WIDTH - run) / 2
    if end_wall < MIN_END_WALL:
        need = ceil((run + 2 * MIN_END_WALL) / BLOCK_WIDTH)
        fix = f"Raise bracket_count to {need}"
        # A single pocket has no pitch to give back, so do not offer it one.
        if pocket_count > 1:
            widest = (
                bracket_count * BLOCK_WIDTH - 2 * MIN_END_WALL - pocket_size
            ) / (pocket_count - 1)
            if widest > 0:
                fix += f", or drop pocket_pitch to {widest:.2f}"
        raise ValueError(
            f"{pocket_count} pockets at {pocket_pitch}mm pitch run {run:.2f}mm across a "
            f"{bracket_count * BLOCK_WIDTH:.2f}mm plate, leaving {end_wall:.2f}mm end walls. "
            f"{fix}."
        )

    back = slab(bracket_count, item_height, item_depth)

    # The block is the pocket wall, and it sits at the bottom of the slab. Above it the
    # pocket region is open air on purpose: a curved plier handle leans out through the
    # gap instead of fouling a full-height wall.
    floor = -item_height
    top = floor + wall_height
    block = Pos((MERGE_X - block_depth) / 2, span(bracket_count), top - wall_height / 2) * Box(
        block_depth + MERGE_X, plate_width(bracket_count), wall_height
    )
    fused = back + block

    # Structural, 3mm, on the one concave edge the whole moment runs through. `new_edges`
    # returns it exactly; a selector for "the edge at x=-item_depth, z=top" would too,
    # right up until something upstream moved.
    body = chamfer(new_edges(back, block, combined=fused), structural_chamfer)

    # Pockets last, and cut the full height rather than only through the block. The
    # relief above is a 3mm ramp reaching forward to x=-9, past the pocket's back wall at
    # x=-7, so a cut that stopped at the block top would leave it bridging over the
    # mouth. Cutting through trims it back to the pocket wall, where it is carried all
    # the way to the bed. See the card: the other order does not build at all.
    mid = span(bracket_count)
    ys = [mid + (k - (pocket_count - 1) / 2) * pocket_pitch for k in range(pocket_count)]
    reach = item_height + 2 * OVERSHOOT
    body -= Part() + [
        Pos((pocket_front + pocket_back) / 2, y, OVERSHOOT - reach / 2)
        * Box(pocket_size, pocket_size, reach)
        for y in ys
    ]
    if draft:
        return body

    # Cosmetic, 1mm, on everything left. Nothing is subtracted here and nothing needs to
    # be: chamfering a concave edge leaves two shallower concave edges, so the structural
    # relief vetoes its own boundary through `polish_edges`, and the pocket walls are
    # inside corners for the same reason. The pocket rims are convex and do get polished,
    # which is what makes the mouths read as finished rather than sawn.
    return polish(body, polish_edges(body, item_height), chamfer_size)
