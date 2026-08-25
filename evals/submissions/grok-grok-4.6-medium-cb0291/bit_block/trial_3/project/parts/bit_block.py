from nurb import *

CLEARANCE = 0.3
WALL = 2.0
ROWS = 2
POCKET_DEPTH = 12.0
FLOOR = 3.0
LEAD_IN = 0.8


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: bit shank width the pockets are sized for
    columns: how many pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_dia = shank_diameter + CLEARANCE
    pocket_r = pocket_dia / 2.0
    pitch = pocket_dia + WALL
    length = columns * pitch + WALL
    width = ROWS * pitch + WALL
    height = POCKET_DEPTH + FLOOR

    if pocket_dia <= 2 * LEAD_IN:
        reject(
            f"shank_diameter {shank_diameter} leaves pockets too small for the 0.8 lead-in",
            param="shank_diameter",
        )

    body = Box(length, width, height)
    z_min = -height / 2.0
    pocket_floor = z_min + FLOOR

    pockets = []
    for col in range(columns):
        for row in range(ROWS):
            x = (col - (columns - 1) / 2.0) * pitch
            y = (row - (ROWS - 1) / 2.0) * pitch
            cut = Cylinder(
                pocket_r,
                POCKET_DEPTH + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            pockets.append(Pos(x, y, pocket_floor) * cut)
    body = body - pockets

    if draft:
        return body

    top_z = body.bounding_box().max.Z
    rims = body.edges().filter_by(GeomType.CIRCLE).filter_by(
        lambda e: abs(e.center().Z - top_z) < 1e-4
    )
    outer_top = body.edges().filter_by(GeomType.LINE).filter_by(
        lambda e: abs(e.bounding_box().min.Z - top_z) < 1e-4
        and abs(e.bounding_box().max.Z - top_z) < 1e-4
    )
    return polish(body, rims + outer_top, LEAD_IN)
