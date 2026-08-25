from nurb import *

WALL = 2.0
FLOOR = 3.0
POCKET_DEPTH = 12.0
CLEARANCE = 0.3
LEAD_IN = 0.8
ROWS = 2


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: across the bit shank
    columns: how many pockets in each row
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_dia = shank_diameter + CLEARANCE
    radius = pocket_dia / 2.0
    if radius <= LEAD_IN:
        reject(
            f"shank_diameter {shank_diameter} is too small for the "
            f"{LEAD_IN}mm mouth chamfer: raise it above {2 * LEAD_IN - CLEARANCE}",
            param="shank_diameter",
        )

    pitch = pocket_dia + WALL
    length = (columns - 1) * pitch + pocket_dia + 2 * WALL
    width = (ROWS - 1) * pitch + pocket_dia + 2 * WALL
    height = FLOOR + POCKET_DEPTH

    body = Box(length, width, height, align=(Align.MIN, Align.MIN, Align.MIN))

    overshoot = 1.0
    pockets = None
    for col in range(columns):
        for row in range(ROWS):
            x = WALL + radius + col * pitch
            y = WALL + radius + row * pitch
            cyl = Pos(x, y, FLOOR) * Cylinder(
                radius,
                POCKET_DEPTH + overshoot,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            pockets = cyl if pockets is None else pockets + cyl
    body = body - pockets

    if draft:
        return body

    top_z = height
    mouths = [
        e
        for e in body.edges().filter_by(GeomType.CIRCLE)
        if abs(e.center().Z - top_z) < 1e-4
    ]
    outer = [
        e
        for e in body.edges().filter_by(GeomType.LINE)
        if abs(e.bounding_box().min.Z - top_z) < 1e-4
        and abs(e.bounding_box().max.Z - top_z) < 1e-4
    ]
    body = chamfer(mouths + outer, LEAD_IN)
    return body
