from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
):
    """A compact bench block that holds two rows of driver bits upright.

    shank_diameter: measured width across each bit shank
    columns: number of bit pockets in each row
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0.0:
        reject("shank_diameter must be greater than 0", param="shank_diameter")

    clearance = 0.3
    wall_between_pockets = 2.0
    side_wall = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    chamfer_size = 0.8
    rows = 2

    pocket_diameter = shank_diameter + clearance
    pitch = pocket_diameter + wall_between_pockets
    block_width = pocket_diameter + (columns - 1) * pitch + 2 * side_wall
    block_depth = pocket_diameter + (rows - 1) * pitch + 2 * side_wall
    block_height = pocket_depth + floor_thickness

    block = Box(
        block_width,
        block_depth,
        block_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    pockets = None
    for row in range(rows):
        y = (row - (rows - 1) / 2) * pitch
        for column in range(columns):
            x = (column - (columns - 1) / 2) * pitch
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_diameter / 2,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            pockets = pocket if pockets is None else pockets + pocket

    block = block - pockets

    top_edges = block.edges().filter_by(
        lambda edge: (
            abs(edge.bounding_box().min.Z - block_height) < 1e-6
            and abs(edge.bounding_box().max.Z - block_height) < 1e-6
        )
    )
    return chamfer(top_edges, length=chamfer_size)
