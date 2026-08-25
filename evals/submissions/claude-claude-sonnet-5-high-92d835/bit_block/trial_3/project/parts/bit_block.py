from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """
    shank_diameter: diameter of the bit shank each pocket holds
    columns: how many pocket columns across the block
    """
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    rows = 2
    pocket_clearance = 0.3
    pocket_dia = shank_diameter + pocket_clearance
    pocket_depth = 12.0
    wall_gap = 2.0  # material left between neighbouring pocket walls
    edge_margin = 2.0  # material from the outermost pocket wall to the block side
    floor_thickness = 3.0
    chamfer_size = 0.8

    pitch = pocket_dia + wall_gap
    height = floor_thickness + pocket_depth
    length = pitch * (columns - 1) + pocket_dia + 2 * edge_margin
    width = pitch * (rows - 1) + pocket_dia + 2 * edge_margin

    body = Box(length, width, height)
    top = body.bounding_box().max.Z

    x_positions = [(i - (columns - 1) / 2) * pitch for i in range(columns)]
    y_positions = [(j - (rows - 1) / 2) * pitch for j in range(rows)]

    for x in x_positions:
        for y in y_positions:
            pocket = Pos(x, y, top - pocket_depth / 2) * Cylinder(pocket_dia / 2, pocket_depth)
            body -= pocket

    if draft:
        return body

    keep = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top) < 1e-6 and abs(e.bounding_box().max.Z - top) < 1e-6
    )
    return polish(body, keep, chamfer_size)
