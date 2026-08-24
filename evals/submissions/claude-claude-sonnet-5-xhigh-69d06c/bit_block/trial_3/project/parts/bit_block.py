from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """
    shank_diameter: diameter of the driver bit shanks the pockets hold
    columns: how many pocket columns run across the block (2 rows fixed)
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    rows = 2
    pocket_clearance = 0.3
    pocket_diameter = shank_diameter + pocket_clearance
    pocket_depth = 12.0
    floor_thickness = 3.0
    wall_margin = 2.0
    pocket_gap = 2.0
    chamfer_size = 0.8

    height = floor_thickness + pocket_depth
    pitch = pocket_diameter + pocket_gap
    width = (columns - 1) * pitch + pocket_diameter + 2 * wall_margin
    depth = (rows - 1) * pitch + pocket_diameter + 2 * wall_margin

    body = Box(width, depth, height)
    if draft:
        return body

    top = height / 2
    overshoot = 1.0
    for i in range(columns):
        x = (i - (columns - 1) / 2) * pitch
        for j in range(rows):
            y = (j - (rows - 1) / 2) * pitch
            pocket = Cylinder(
                pocket_diameter / 2,
                pocket_depth + overshoot,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - Pos(x, y, top - pocket_depth) * pocket

    # Pocket mouths and the top perimeter are exactly the edges lying flat
    # in the top plane; corner and bottom edges never enter this set.
    lead_in_edges = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top) < 1e-6
        and abs(e.bounding_box().max.Z - top) < 1e-6
    )
    return chamfer(lead_in_edges, chamfer_size)
