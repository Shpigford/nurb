from nurb import *

ROWS = 2
CLEARANCE = 0.3
WALL = 2.0
POCKET_DEPTH = 12.0
FLOOR = 3.0
LEAD_IN = 0.8


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: measured width of a bit shank; pockets are this plus 0.3 of clearance
    columns: number of pockets along the long side; two rows deep
    """
    shank_diameter = float(shank_diameter)
    columns = int(columns)
    if columns < 1:
        reject("columns must be at least 1 so there is a pocket to drop a bit into", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_dia = shank_diameter + CLEARANCE
    if pocket_dia <= 2 * LEAD_IN:
        reject(
            f"shank_diameter {shank_diameter} leaves a {pocket_dia}mm pocket, "
            f"too small for the {LEAD_IN}mm mouth chamfer; raise it above {2 * LEAD_IN - CLEARANCE}",
            param="shank_diameter",
        )

    pitch = pocket_dia + WALL
    height = POCKET_DEPTH + FLOOR
    length = columns * pocket_dia + (columns + 1) * WALL
    depth = ROWS * pocket_dia + (ROWS + 1) * WALL

    body = Box(length, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    radius = pocket_dia / 2
    first_x = WALL + radius
    first_y = WALL + radius
    overcut = 1.0
    cut = None
    for col in range(columns):
        for row in range(ROWS):
            x = first_x + col * pitch
            y = first_y + row * pitch
            pocket = Pos(x, y, FLOOR) * Cylinder(
                radius,
                POCKET_DEPTH + overcut,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            cut = pocket if cut is None else cut + pocket
    body -= cut

    # Functional lead-in and top-rim chamfers, not the 1mm polish pass: every other
    # edge stays sharp, including the bottom perimeter so the bounding box is exact.
    top = height
    rim = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top) < 1e-4
        and abs(e.bounding_box().max.Z - top) < 1e-4
    )
    return chamfer(rim, LEAD_IN)
