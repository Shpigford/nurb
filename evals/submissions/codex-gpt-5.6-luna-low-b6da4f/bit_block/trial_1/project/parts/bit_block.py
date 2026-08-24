from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """Upright bit holder.

    shank_diameter: diameter of the bit shanks
    columns: number of pockets in the long direction
    """
    pitch = 8.3
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pocket_depth = 12.0
    floor = 3.0
    lead = 0.8
    rows = 2
    width = 2.0 + pocket_diameter + (columns - 1) * pitch + 2.0
    depth = 2.0 + pocket_diameter + (rows - 1) * pitch + 2.0
    height = floor + pocket_depth

    body = Box(width, depth, height)
    for column in range(columns):
        for row in range(rows):
            x = -width / 2.0 + 2.0 + pocket_radius + column * pitch
            y = -depth / 2.0 + 2.0 + pocket_radius + row * pitch
            straight = Cylinder(pocket_radius, pocket_depth - lead).translate(
                (x, y, -height / 2.0 + floor)
            )
            body = body.cut(straight)

    top = body.bounding_box().max.Z
    top_edges = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 0.001
    )
    body = polish(body, top_edges, lead)
    return body
