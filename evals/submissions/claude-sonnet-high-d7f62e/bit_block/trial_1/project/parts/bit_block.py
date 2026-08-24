from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """A bench block that holds driver bits upright in round pockets.

    shank_diameter: the bit shank's diameter that each pocket must clear
    columns: how many pocket columns run along the block's long side
    """
    rows = 2
    clearance = 0.3
    wall = 2.0
    margin = 2.0
    pocket_depth = 12.0
    floor = 3.0
    chamfer_size = 0.8

    if columns < 1:
        reject(f"columns {columns} is under 1: a grid needs at least one column", param="columns")
    if shank_diameter <= 0:
        reject(f"shank_diameter {shank_diameter} is not a positive size", param="shank_diameter")

    pocket_dia = shank_diameter + clearance
    pitch = pocket_dia + wall
    height = pocket_depth + floor

    block_x = (columns - 1) * pitch + pocket_dia + 2 * margin
    block_y = (rows - 1) * pitch + pocket_dia + 2 * margin

    block = Pos(0, 0, height / 2) * Box(block_x, block_y, height)

    x0 = -(columns - 1) * pitch / 2
    y0 = -(rows - 1) * pitch / 2

    for col in range(columns):
        for row in range(rows):
            x = x0 + col * pitch
            y = y0 + row * pitch
            pocket = Pos(x, y, height - pocket_depth / 2) * Cylinder(pocket_dia / 2, pocket_depth)
            block = block - pocket

    top_face = block.faces().filter_by(
        lambda f: f.normal_at().Z > 0.5 and abs(f.center().Z - height) < 1e-6
    )[0]

    return chamfer(list(top_face.edges()), chamfer_size)
