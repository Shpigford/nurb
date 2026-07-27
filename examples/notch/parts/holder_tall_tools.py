"""Holder - Tall Tools - 5x. Read holder_tall_tools.md before changing anything."""

from math import floor

from nurb import *

from system import (
    BLOCK_WIDTH,
    DETENT_DEPTH,
    EPS,
    FLOOR_X,
    MIN_ITEM_DEPTH,
    channels,
    detent_dimples,
    plate_width,
    polish,
    polish_edges,
    span,
)


@part
def holder_tall_tools(
    bracket_count=5,
    item_height=55.0,
    item_depth=6.0,
    slot_count=6,
    slot_width=17.0,
    slot_depth=17.0,
    slot_wall=3.0,
    slot_cut=45.0,
    floor_thick=4.0,
    front_wall=4.0,
    block_overlap=1.0,
    chamfer_size=1.0,
    # Declared but unused, and deliberately so: opening the pocket backs left no
    # load-bearing concave junction to relieve. The card says what it would relieve if a
    # variant ever closes the backs again.
    structural_chamfer=3.0,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"block would not reach the slab. Raise it above {MIN_ITEM_DEPTH}."
        )

    # The row is what sets this part's bracket count, not the other way round. Both walls
    # either side of a divider get polished, so a divider narrower than twice the chamfer
    # leaves the kernel no corner to build: measured at 2.05mm building and 2.00mm
    # failing, on the end walls, the dividers and the front wall alike.
    plate = bracket_count * BLOCK_WIDTH
    row = slot_count * slot_width + (slot_count - 1) * slot_wall
    end_wall = (plate - row) / 2
    if end_wall <= 2 * chamfer_size:
        fits = int((plate - 4 * chamfer_size + slot_wall) // (slot_width + slot_wall))
        need = floor((row + 4 * chamfer_size) / BLOCK_WIDTH) + 1
        raise ValueError(
            f"{slot_count} slots need {row:.2f}mm of row, which leaves {end_wall:.2f}mm of end "
            f"wall on a {plate:.2f}mm plate. Drop slot_count to {fits}, or raise bracket_count "
            f"to {need}."
        )

    # 1mm of overlap is not arbitrary: it is exactly what is left between the slab's front
    # face and the floor of the detent dimple. Any more and the block fills the dimple,
    # which builds and prints and quietly stops the part latching to the wall.
    block_back = -(item_depth - block_overlap)
    room = item_depth + FLOOR_X - DETENT_DEPTH
    if not 0 < block_overlap <= room + EPS:  # EPS: the default lands exactly on `room`
        raise ValueError(
            f"block_overlap {block_overlap} puts the block's back face at x={block_back:.2f}, "
            f"where it either misses the slab or fills the detent dimple. Keep it above 0 and "
            f"no more than {room:.2f}."
        )

    plate = Pos(-item_depth / 2, span(bracket_count), -item_height / 2) * Box(
        item_depth, plate_width(bracket_count), item_height
    )

    # The block is grounded on the bed and flush with the plate at the sides, so its own
    # sides are the slab's and no side strip stands beside it. What is left above it is
    # the reveal, and that band has to stay taller than the chamfer that lands on it.
    block_top = -(item_height - slot_cut - floor_thick)
    block_front = -(item_depth + slot_depth + front_wall)
    block = Pos(
        (block_front + block_back) / 2, span(bracket_count), (block_top - item_height) / 2
    ) * Box(block_back - block_front, plate_width(bracket_count), item_height + block_top)

    # The slab is the pocket back. Each cut stops on the slab's own front face, so a tool
    # leans on the full slab and nothing is spent on a back wall; the two coplanar faces
    # come back as one, which is why there is no rim to polish along the mouth's back.
    # Reaching any further back would eat the 1.8mm web in front of the channels.
    mouth = Pos(0, span(bracket_count), block_top)
    pocket = Pos(-(item_depth + slot_depth / 2), 0, -slot_cut / 2) * Box(
        slot_depth, slot_width, slot_cut
    )
    step = slot_width + slot_wall
    first = -(slot_count - 1) * step / 2
    pockets = Part() + [mouth * Pos(0, first + i * step, 0) * pocket for i in range(slot_count)]

    # Cut after the fuse, not before. The dimple floor and the block's back face are the
    # same plane, so subtracting the dimples from the slab first would leave the two
    # solids meeting face to face there instead of overlapping.
    body = (
        (plate + block)
        - channels(bracket_count, item_height)
        - detent_dimples(bracket_count)
        - pockets
    )
    if draft:
        return body

    # Cosmetic, 1mm, and the only pass this part gets. The standing vetoes cover it: the
    # seven root segments where the block top meets the slab are concave, and so is
    # everything inside a pocket.
    return polish(body, polish_edges(body, item_height), chamfer_size)
