from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5):
    """
    shank_diameter: diameter of the driver bit shanks the pockets hold
    columns: how many pocket columns run across the block
    """
    wall = 2.0
    rows = 2
    pocket_dia = shank_diameter + 0.3
    pocket_depth = 12.0
    floor = 3.0
    height = floor + pocket_depth
    pitch = pocket_dia + wall

    block_x = columns * pocket_dia + (columns + 1) * wall
    block_y = rows * pocket_dia + (rows + 1) * wall

    body = Box(
        block_x, block_y, height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    for i in range(columns):
        cx = -block_x / 2 + wall + pocket_dia / 2 + i * pitch
        for j in range(rows):
            cy = -block_y / 2 + wall + pocket_dia / 2 + j * pitch
            pocket = Cylinder(
                pocket_dia / 2, pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            pocket = Pos(cx, cy, height - pocket_depth) * pocket
            body -= pocket

    top_z = height
    lead_in_edges = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top_z) < 1e-6
        and abs(e.bounding_box().max.Z - top_z) < 1e-6
    )

    return polish(body, lead_in_edges, 0.8)
