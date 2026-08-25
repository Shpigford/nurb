from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """A compact bench block that stores driver bits upright.

    shank_diameter: measured width of each bit's round shank
    columns: number of pockets across the long side of the block
    """
    clearance = 0.3
    pocket_diameter = shank_diameter + clearance
    pocket_radius = pocket_diameter / 2.0
    wall = 2.0
    pitch = pocket_diameter + wall
    rows = 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = pocket_depth + floor_thickness
    width = 2.0 * wall + pocket_diameter + (columns - 1) * pitch
    depth = 2.0 * wall + pocket_diameter + (rows - 1) * pitch

    body = Box(width, depth, height)
    bounds = body.bounding_box()

    first_x = bounds.min.X + wall + pocket_radius
    first_y = bounds.min.Y + wall + pocket_radius
    pocket_floor = bounds.min.Z + floor_thickness
    top_z = bounds.max.Z
    lead_in = 0.8
    for column in range(columns):
        for row in range(rows):
            center_x = first_x + column * pitch
            center_y = first_y + row * pitch
            pocket = Cylinder(pocket_radius, pocket_depth).translate(
                (center_x, center_y, pocket_floor + pocket_depth / 2.0)
            )
            mouth = Cone(
                pocket_radius, pocket_radius + lead_in, lead_in
            ).translate(
                (center_x, center_y, top_z - lead_in / 2.0)
            )
            body = body - pocket - mouth

    top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z >= top_z - 0.001
    )
    return polish(body, top_edges, lead_in)
