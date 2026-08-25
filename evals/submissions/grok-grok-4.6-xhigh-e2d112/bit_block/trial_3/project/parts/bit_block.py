from nurb import *

# 0.3mm extra so a measured shank drops in (the moving/free fit).
POCKET_CLEARANCE = 0.3
WALL = 2.0
POCKET_DEPTH = 12.0
FLOOR_THICKNESS = 3.0
LEAD_IN = 0.8
ROWS = 2


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """Hold driver bits upright in a grid of round pockets.

    shank_diameter: bit shank across, from the calipers
    columns: how many pockets along the long side
    """
    if columns < 1:
        reject("columns must be at least 1 to hold any bits", param="columns")

    pocket_diameter = shank_diameter + POCKET_CLEARANCE
    if pocket_diameter < 2.0:
        reject(
            f"pocket diameter {pocket_diameter:.1f} is under 2mm and will not print; "
            "raise shank_diameter so the pocket is at least 2mm",
            param="shank_diameter",
        )

    pitch = pocket_diameter + WALL
    height = POCKET_DEPTH + FLOOR_THICKNESS
    length = columns * pitch + WALL
    width = ROWS * pitch + WALL

    block = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if not draft:
        top = block.faces().sort_by(Axis.Z)[-1]
        block = chamfer(top.edges(), LEAD_IN)

    radius = pocket_diameter / 2
    x0 = -length / 2 + WALL + radius
    y0 = -width / 2 + WALL + radius
    # Overshoot the top so the 45-degree lead-in cuts through the top face cleanly.
    cone_height = LEAD_IN + 1.0

    for col in range(columns):
        for row in range(ROWS):
            x = x0 + col * pitch
            y = y0 + row * pitch
            shaft = Pos(x, y, FLOOR_THICKNESS) * Cylinder(
                radius,
                POCKET_DEPTH + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            mouth = Pos(x, y, height - LEAD_IN) * Cone(
                radius,
                radius + cone_height,
                cone_height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block -= shaft + mouth

    return block
