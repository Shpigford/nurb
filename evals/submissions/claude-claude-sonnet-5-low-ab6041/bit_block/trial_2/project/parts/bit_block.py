from nurb import *

ROWS = 2
EDGE_MARGIN = 2.0
FLOOR_THICKNESS = 3.0
POCKET_DEPTH = 12.0
CHAMFER = 0.8


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """
    shank_diameter: how wide the bit shanks measure across
    columns: how many pockets sit in each row
    """
    pocket_dia = shank_diameter + 0.3
    pitch = pocket_dia + 2.0  # 2mm of wall between neighbouring pocket walls

    width = (columns - 1) * pitch + pocket_dia + 2 * EDGE_MARGIN
    depth = (ROWS - 1) * pitch + pocket_dia + 2 * EDGE_MARGIN
    height = FLOOR_THICKNESS + POCKET_DEPTH

    body = Box(width, depth, height)

    top_z = height / 2
    pocket_bottom_z = top_z - POCKET_DEPTH

    for col in range(columns):
        x = -(columns - 1) * pitch / 2 + col * pitch
        for row in range(ROWS):
            y = -(ROWS - 1) * pitch / 2 + row * pitch
            pocket = Pos(x, y, pocket_bottom_z) * Cylinder(
                pocket_dia / 2, POCKET_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            body -= pocket

    if draft:
        return body

    top_edges = body.edges().filter_by(lambda e: e.bounding_box().min.Z >= top_z - 1e-6)
    return polish(body, top_edges, CHAMFER)
