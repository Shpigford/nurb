from nurb import *

# Bit shanks sit in round pockets; 0.3 mm is the print clearance on the measured
# shank, 2 mm is the wall between pockets and around the perimeter.
POCKET_CLEARANCE = 0.3
WALL = 2.0
POCKET_DEPTH = 12.0
FLOOR = 3.0
ROWS = 2
LEAD_IN = 0.8


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: measured bit-shank width; pockets are this plus 0.3 mm clearance
    columns: number of pockets across the long side
    """
    shank_diameter = float(shank_diameter)
    columns = int(columns)
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_dia = shank_diameter + POCKET_CLEARANCE
    pitch = pocket_dia + WALL
    length = (columns + 1) * WALL + columns * pocket_dia
    width = (ROWS + 1) * WALL + ROWS * pocket_dia
    height = POCKET_DEPTH + FLOOR

    body = Box(length, width, height)
    first_x = -length / 2 + WALL + pocket_dia / 2
    first_y = -width / 2 + WALL + pocket_dia / 2
    for col in range(columns):
        for row in range(ROWS):
            x = first_x + col * pitch
            y = first_y + row * pitch
            cutter = Cylinder(
                pocket_dia / 2,
                POCKET_DEPTH + 0.02,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).move(Location((x, y, -height / 2 + FLOOR)))
            body = body - cutter

    if draft:
        return body

    top_z = body.bounding_box().max.Z
    mouths_and_rim = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top_z) < 1e-3
        and abs(e.bounding_box().max.Z - top_z) < 1e-3
    )
    return chamfer(mouths_and_rim, LEAD_IN)
