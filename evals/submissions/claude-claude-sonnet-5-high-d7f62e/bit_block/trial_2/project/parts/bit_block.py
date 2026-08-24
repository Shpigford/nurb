from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """
    shank_diameter: how wide the bit shanks are across
    columns: how many pockets sit side by side
    """
    rows = 2
    pocket_clearance = 0.3
    pocket_gap = 2.0
    wall_margin = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    chamfer_size = 0.8

    pocket_dia = shank_diameter + pocket_clearance
    pitch = pocket_dia + pocket_gap

    height = pocket_depth + floor_thickness
    width = 2 * wall_margin + pocket_dia + (columns - 1) * pitch
    depth = 2 * wall_margin + pocket_dia + (rows - 1) * pitch

    body = Box(width, depth, height)

    top_z = height / 2
    x0 = -(columns - 1) * pitch / 2
    y0 = -(rows - 1) * pitch / 2
    for c in range(columns):
        for r in range(rows):
            x = x0 + c * pitch
            y = y0 + r * pitch
            pocket = Pos(x, y, top_z - pocket_depth / 2) * Cylinder(
                pocket_dia / 2, pocket_depth
            )
            body -= pocket

    if draft:
        return body

    top = body.bounding_box().max.Z
    lead_in = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z >= top - 1e-6
        and e.bounding_box().max.Z >= top - 1e-6
    )
    return polish(body, lead_in, chamfer_size)
