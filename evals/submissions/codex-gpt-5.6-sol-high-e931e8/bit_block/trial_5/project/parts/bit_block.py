from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
):
    """A compact bench block that holds two rows of driver bits upright.

    shank_diameter: measured width of each driver's round shank
    columns: number of bit pockets in each row
    """
    if shank_diameter <= 1.7:
        reject(
            "shank_diameter must be above 1.7 mm so the finished pocket is printable",
            param="shank_diameter",
        )
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    clearance = 0.3
    wall = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    chamfer_size = 0.8
    rows = 2

    pocket_diameter = shank_diameter + clearance
    pitch = pocket_diameter + wall
    block_width = columns * pocket_diameter + (columns - 1) * wall + 2 * wall
    block_depth = rows * pocket_diameter + (rows - 1) * wall + 2 * wall
    block_height = pocket_depth + floor_thickness

    block = Box(
        block_width,
        block_depth,
        block_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    first_x = -0.5 * (columns - 1) * pitch
    first_y = -0.5 * (rows - 1) * pitch
    for row in range(rows):
        for column in range(columns):
            x = first_x + column * pitch
            y = first_y + row * pitch
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_diameter / 2,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - pocket

    top_edges = block.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - block_height) < 1e-6
        and abs(edge.bounding_box().max.Z - block_height) < 1e-6
    )
    return chamfer(top_edges, length=chamfer_size)
