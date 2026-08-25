from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """A compact upright holder for 6 mm driver bits.

    shank_diameter: measured width across each bit shank
    columns: number of pockets across the block
    """
    clearance = 0.3
    pocket_diameter = shank_diameter + clearance
    pocket_radius = pocket_diameter / 2
    pitch = 8.3
    edge_wall = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    width = 2 * edge_wall + pocket_diameter + (columns - 1) * pitch
    depth = 2 * edge_wall + pocket_diameter + pitch

    body = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))
    # The block's lower outside edges intentionally remain sharp.
    top_perimeter = body.edges().filter_by_position(Axis.Z, height, height)
    body = chamfer(top_perimeter, 0.8)

    for row in range(2):
        for column in range(columns):
            x = edge_wall + pocket_radius + column * pitch
            y = edge_wall + pocket_radius + row * pitch
            straight = Cylinder(
                pocket_radius, pocket_depth - 0.8,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).translate((x, y, floor_thickness))
            lead_in = Cone(
                pocket_radius, pocket_radius + 0.8, 0.8,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).translate((x, y, height - 0.8))
            body = body - straight - lead_in

    return body
