from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """Bench block for upright driver bits.

    shank_diameter: measured width of a bit shank.
    columns: number of pockets across the long side.
    """
    clearance = 0.3
    pocket_diameter = shank_diameter + clearance
    pocket_radius = pocket_diameter / 2
    wall = 2.0
    pitch = pocket_diameter + wall
    rows = 2
    floor_thickness = 3.0
    pocket_depth = 12.0
    height = floor_thickness + pocket_depth
    width = columns * pocket_diameter + (columns - 1) * wall + 2 * wall
    depth = rows * pocket_diameter + (rows - 1) * wall + 2 * wall

    body = Box(width, depth, height)
    top_outer_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z >= 0
    )
    body = polish(body, top_outer_edges, 0.8)
    pocket_floor_z = -height / 2 + floor_thickness
    straight_bore_height = pocket_depth - 0.8
    for row in range(rows):
        for column in range(columns):
            x = -width / 2 + wall + pocket_radius + column * pitch
            y = -depth / 2 + wall + pocket_radius + row * pitch
            straight_bore = Cylinder(pocket_radius, straight_bore_height).translate(
                (x, y, pocket_floor_z + straight_bore_height / 2)
            )
            lead_in = Cone(pocket_radius, pocket_radius + 0.8, 0.8).translate(
                (x, y, height / 2 - 0.4)
            )
            pocket = straight_bore.fuse(lead_in)
            body = body.cut(pocket)
    return body
