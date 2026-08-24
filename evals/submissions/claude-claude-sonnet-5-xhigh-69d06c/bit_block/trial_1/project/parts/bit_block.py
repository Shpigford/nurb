from nurb import *

GAP = 2.0  # material between neighbouring pocket walls, and from the outer pockets to the sides
ROWS = 2
POCKET_DEPTH = 12.0
FLOOR_THICKNESS = 3.0
CHAMFER = 0.8


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """
    shank_diameter: how wide the bit shanks measure across
    columns: how many pocket columns run along the long edge
    """
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_dia = shank_diameter + 0.3
    pitch = pocket_dia + GAP
    height = FLOOR_THICKNESS + POCKET_DEPTH

    width = (columns - 1) * pitch + pocket_dia + 2 * GAP
    depth = (ROWS - 1) * pitch + pocket_dia + 2 * GAP

    body = Box(width, depth, height)

    top_z = height / 2
    pocket = Cylinder(pocket_dia / 2, POCKET_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MAX))

    x_centers = [-(columns - 1) * pitch / 2 + i * pitch for i in range(columns)]
    y_centers = [-(ROWS - 1) * pitch / 2 + j * pitch for j in range(ROWS)]

    for x in x_centers:
        for y in y_centers:
            body -= Pos(x, y, top_z) * pocket

    if draft:
        return body

    mouths = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top_z) < 1e-6
        and abs(e.bounding_box().max.Z - top_z) < 1e-6
    )
    return polish(body, mouths, CHAMFER)
