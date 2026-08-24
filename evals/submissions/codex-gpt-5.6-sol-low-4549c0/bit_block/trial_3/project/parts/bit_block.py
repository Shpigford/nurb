from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
):
    """A compact bench block that holds driver bits upright.

    shank_diameter: measured diameter across each bit's round shank
    columns: number of bit pockets in each of the two rows
    """
    pocket_diameter = shank_diameter + 0.3
    wall = 2.0
    pitch = pocket_diameter + wall
    edge_margin = wall
    rows = 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    block_height = pocket_depth + floor_thickness
    block_width = pocket_diameter + (columns - 1) * pitch + 2.0 * edge_margin
    block_depth = pocket_diameter + (rows - 1) * pitch + 2.0 * edge_margin

    body = Box(block_width, block_depth, block_height)

    for row in range(rows):
        for column in range(columns):
            x = (column - (columns - 1) / 2.0) * pitch
            y = (row - (rows - 1) / 2.0) * pitch
            pocket_z = -block_height / 2.0 + floor_thickness + pocket_depth / 2.0
            pocket = Pos(x, y, pocket_z) * Cylinder(
                pocket_diameter / 2.0,
                pocket_depth,
            )
            body = body - pocket

    top_z = body.bounding_box().max.Z
    top_edges = [
        edge
        for edge in body.edges()
        if abs(edge.bounding_box().min.Z - top_z) < 1e-6
        and abs(edge.bounding_box().max.Z - top_z) < 1e-6
    ]
    return chamfer(top_edges, 0.8)
