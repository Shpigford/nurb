from nurb import *

# Fit and structure. Pocket walls stay WALL apart and WALL from the sides, so
# pitch and the block's footprint both follow shank_diameter and columns.
CLEARANCE = 0.3
WALL = 2.0
POCKET_DEPTH = 12.0
FLOOR = 3.0
LEAD_IN = 0.8
ROWS = 2


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: measured width of a bit shank
    columns: number of pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1 to hold any bits", param="columns")
    pocket_dia = shank_diameter + CLEARANCE
    if pocket_dia <= 2 * LEAD_IN:
        reject(
            f"shank_diameter {shank_diameter} leaves a {pocket_dia}mm pocket, "
            f"too small for a {LEAD_IN}mm lead-in; raise it above {2 * LEAD_IN - CLEARANCE}",
            param="shank_diameter",
        )

    pitch = pocket_dia + WALL
    length = WALL + columns * pitch
    width = WALL + ROWS * pitch
    height = FLOOR + POCKET_DEPTH

    body = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    x0 = -(columns - 1) * pitch / 2
    y0 = -(ROWS - 1) * pitch / 2
    radius = pocket_dia / 2
    # Overshoot the top so the pocket is open; sit the cutter on the floor so
    # the pocket is exactly POCKET_DEPTH with a flat bottom.
    cutter_h = POCKET_DEPTH + 1.0
    for col in range(columns):
        for row in range(ROWS):
            x = x0 + col * pitch
            y = y0 + row * pitch
            cutter = Cylinder(
                radius,
                cutter_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body -= Pos(x, y, FLOOR) * cutter

    if draft:
        return body

    # Pocket mouths and the top outer perimeter only. Bottom and verticals stay
    # sharp so the bounding box is the uncut block.
    top = body.faces().sort_by(Axis.Z)[-1]
    return chamfer(top.edges(), LEAD_IN)
