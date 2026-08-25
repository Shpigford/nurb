from nurb import *


@part
def bit_block(
    shank_diameter: float = 6.0,
    columns: int = 5,
):
    """Bench block for upright driver bits.

    shank_diameter: measured diameter of the bit shanks
    columns: number of pockets across the block
    """
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    wall = 2.0
    pitch = pocket_diameter + wall
    rows = 2
    floor_thickness = 3.0
    pocket_depth = 12.0
    height = floor_thickness + pocket_depth

    width = 2 * wall + pocket_diameter + (columns - 1) * pitch
    depth = 2 * wall + pocket_diameter + (rows - 1) * pitch

    body = Box(width, depth, height)
    pocket_floor = -height / 2 + floor_thickness
    lead_in_start = height / 2 - 0.8
    for row in range(rows):
        for column in range(columns):
            x = -width / 2 + wall + pocket_radius + column * pitch
            y = -depth / 2 + wall + pocket_radius + row * pitch
            pocket = Cylinder(pocket_radius, lead_in_start - pocket_floor).translate(
                (x, y, (pocket_floor + lead_in_start) / 2)
            )
            lead_in = Cone(pocket_radius, pocket_radius + 0.8, 0.8).translate(
                (x, y, lead_in_start + 0.4)
            )
            body = body - pocket - lead_in

    top_outer_edges = body.edges().filter_by(GeomType.LINE).filter_by_position(
        Axis.Z, height / 2, height / 2
    )
    return body.chamfer(0.8, 0.8, top_outer_edges)
