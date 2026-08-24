from nurb import *

CLEARANCE = 0.3
POCKET_DEPTH = 12.0
FLOOR = 3.0
WALL = 2.0
LEAD_IN = 0.8
ROWS = 2


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: width of a bit shank; pockets are this plus 0.3mm of clearance
    columns: number of pockets along the long side
    """
    if columns < 1:
        reject(
            "columns must be at least 1 so there is a pocket to stand a bit in",
            param="columns",
        )
    if shank_diameter <= 0:
        reject(
            "shank_diameter must be greater than 0",
            param="shank_diameter",
        )

    pocket_dia = shank_diameter + CLEARANCE
    if pocket_dia <= 2 * LEAD_IN:
        reject(
            f"shank_diameter {shank_diameter} leaves a {pocket_dia}mm pocket, "
            f"too tight for a {LEAD_IN}mm lead-in: raise it above "
            f"{2 * LEAD_IN - CLEARANCE}",
            param="shank_diameter",
        )

    pitch = pocket_dia + WALL
    length = (columns - 1) * pitch + pocket_dia + 2 * WALL
    width = (ROWS - 1) * pitch + pocket_dia + 2 * WALL
    height = POCKET_DEPTH + FLOOR

    body = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    overshoot = 0.5
    x0 = -(columns - 1) * pitch / 2
    y0 = -(ROWS - 1) * pitch / 2
    holes = None
    for i in range(columns):
        for j in range(ROWS):
            hole = Pos(x0 + i * pitch, y0 + j * pitch, FLOOR) * Cylinder(
                pocket_dia / 2,
                POCKET_DEPTH + overshoot,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            holes = hole if holes is None else holes + hole
    body -= holes

    if draft:
        return body

    top = body.faces().sort_by(Axis.Z)[-1]
    return chamfer(top.edges(), LEAD_IN)
