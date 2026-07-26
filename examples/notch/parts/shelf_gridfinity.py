"""Shelf - Gridfinity 2x2 - 4x. Read shelf_gridfinity.md before changing anything."""

from math import floor

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

# The gridfinity baseplate socket, cut down from the platform top. Verified against
# gridfinity-rebuilt-openscad and gridfinity.xyz. Do not tweak these: a bin seats on
# the two 45 degree bands, and the recess at the bottom is what stops it bottoming
# out on the floor before the bands take it.
MOUTH_CHAMFER = 2.15
WALL = 1.80
THROAT_CHAMFER = 0.70
RECESS = 0.35
MOUTH_RADIUS = 4.00
SOCKET_DEPTH = MOUTH_CHAMFER + WALL + THROAT_CHAMFER + RECESS  # 5.0


def socket(cell):
    """One gridfinity pocket, mouth at z=0, opening downward."""
    rings = [
        (0.0, cell, MOUTH_RADIUS),
        (MOUTH_CHAMFER, cell - 2 * MOUTH_CHAMFER, MOUTH_RADIUS - MOUTH_CHAMFER),
        (MOUTH_CHAMFER + WALL, cell - 2 * MOUTH_CHAMFER, MOUTH_RADIUS - MOUTH_CHAMFER),
        (SOCKET_DEPTH - RECESS, cell - 2 * (MOUTH_CHAMFER + THROAT_CHAMFER),
         MOUTH_RADIUS - MOUTH_CHAMFER - THROAT_CHAMFER),
        (SOCKET_DEPTH, cell - 2 * (MOUTH_CHAMFER + THROAT_CHAMFER),
         MOUTH_RADIUS - MOUTH_CHAMFER - THROAT_CHAMFER),
    ]
    return loft(
        [Pos(0, 0, -down) * RectangleRounded(w, w, r) for down, w, r in rings],
        ruled=True,
    )


@part
def shelf_gridfinity(
    bracket_count=4,
    item_height=42,
    item_depth=6,
    grid_x=2,
    grid_y=2,
    cell=42,
    shelf_thickness=7,
    back_gap=4,
    gusset_thickness=3,
    gusset_tip=6,
    gusset_drop=3,
    chamfer_size=1,
    structural_chamfer=3,
    draft=False,
):
    if item_depth <= MIN_ITEM_DEPTH:
        raise ValueError(
            f"item_depth {item_depth} leaves no material behind the channel floor, so the "
            f"platform would not reach the slab. Raise it above {MIN_ITEM_DEPTH}."
        )

    # The slab has to stand wider than the platform, with room to spare: two polished
    # edges closer together than twice the chamfer leave the kernel no corner to
    # build. Same arithmetic as `gusset_drop`, and the reason the grid sizes pair with
    # bracket counts the way they do (1 -> 3, 2 -> 4, 3 -> 6).
    #
    # floor + 1 rather than ceil: the rule needs strictly more room than the chamfers
    # take, so a width that divides exactly still needs the next bracket.
    width = grid_x * cell + 2 * gusset_thickness
    need = floor((width + 4 * chamfer_size) / BLOCK_WIDTH) + 1
    if bracket_count < need:
        raise ValueError(
            f"a {grid_x}-wide grid is {width:.0f}mm across, so it needs {need} brackets, "
            f"not {bracket_count}. Raise bracket_count to {need}, or drop grid_x."
        )

    y0, y1 = -BLOCK_WIDTH / 2, (bracket_count - 0.5) * BLOCK_WIDTH
    slab = Pos(-item_depth / 2, (y0 + y1) / 2, -item_height / 2) * Box(
        item_depth, y1 - y0, item_height
    )
    back = slab - channels(bracket_count, item_height) - detent_dimples(bracket_count)

    # Everything forward hangs off the bracket run's midpoint, not off y=0, so the
    # load stays balanced between the brackets.
    mid = span(bracket_count)
    top = -item_height + shelf_thickness
    front = -(item_depth + back_gap + grid_y * cell)

    platform = Pos((MERGE_X + front) / 2, mid, top - shelf_thickness / 2) * Box(
        MERGE_X - front, width, shelf_thickness
    )
    grid = Pos(-(item_depth + back_gap) - grid_y * cell / 2, mid, top)
    platform -= Part() + [
        grid * place * socket(cell) for place in GridLocations(cell, cell, grid_y, grid_x)
    ]

    # Gussets, which are also the side cheeks. Truncated at the tip rather than run
    # out to a point: a knife edge there is a sliver, and the last few millimeters of
    # a triangle carry no load anyway.
    #
    # `gusset_drop` has to clear twice `chamfer_size`. The peak and the slab top both
    # get polished, and if their chamfer bands meet the kernel cannot build the
    # corner. Fusion failed in the same place with ASM_BL_NO_MATE; OCCT raises
    # "BRep_API: command not done" and needs a little more room than Fusion did.
    section = Plane.XZ * Polygon(
        (MERGE_X, top),
        (-(item_depth + grid_y * cell / 2), top),
        (-(item_depth + grid_y * cell / 2), top + gusset_tip),
        (-item_depth, -gusset_drop),
        (MERGE_X, -gusset_drop),
        align=None,
    )
    cheek = extrude(section, gusset_thickness / 2, both=True)
    reach = (width - gusset_thickness) / 2
    shelf = platform + Part() + [Pos(0, mid + s * reach, 0) * cheek for s in (-1, 1)]

    body = back + shelf
    pristine = body

    # Structural, 3mm: only where the platform lands on the slab. The gusset roots
    # are concave too, but a gusset is 3mm thick, so a 3mm chamfer would eat it.
    junction = [
        e for e in new_edges(back, shelf, combined=body)
        if abs(e.bounding_box().min.Z - top) < EPS and abs(e.bounding_box().max.Z - top) < EPS
    ]
    body = chamfer(junction, structural_chamfer)
    if draft:
        return body

    # Cosmetic, 1mm. On top of the standing vetoes: nothing in the socket band. The
    # mouth rims are spec geometry and read as a real baseplate precisely because
    # they stay knife sharp, and the gusset roots live in that plane too.
    def in_sockets(edge):
        bb = edge.bounding_box()
        return bb.max.Z < top + EPS and bb.min.Z > top - SOCKET_DEPTH - EPS

    polish = polish_edges(body, item_height).filter_by(lambda e: not in_sockets(e))
    return chamfer(polish - new_edges(pristine, combined=body), chamfer_size)
