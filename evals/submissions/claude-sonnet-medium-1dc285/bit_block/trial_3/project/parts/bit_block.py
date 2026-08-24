from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """
    shank_diameter: diameter of the bit shanks each pocket holds
    columns: how many pocket columns across the block's long side
    """
    rows = 2
    pocket_dia = shank_diameter + 0.3
    pocket_depth = 12.0
    wall = 2.0
    pitch = pocket_dia + wall
    floor = 3.0
    height = floor + pocket_depth
    chamfer_size = 0.8

    width = 2 * wall + pocket_dia + (columns - 1) * pitch
    depth = 2 * wall + pocket_dia + (rows - 1) * pitch

    body = Box(width, depth, height)
    bed = body.bounding_box().min.Z
    top = body.bounding_box().max.Z

    x0 = -(columns - 1) * pitch / 2
    y0 = -(rows - 1) * pitch / 2

    cut_len = pocket_depth + 1.0
    pockets = None
    for c in range(columns):
        for r in range(rows):
            x = x0 + c * pitch
            y = y0 + r * pitch
            cyl = Pos(x, y, top - pocket_depth + cut_len / 2) * Cylinder(pocket_dia / 2, cut_len)
            pockets = cyl if pockets is None else pockets + cyl

    body -= pockets

    if draft:
        return body

    # Pocket mouths and the top outer perimeter are the only edges lying flat
    # in the top plane; every other exposed edge, including the whole bottom
    # perimeter, is left sharp.
    keep = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top) < 1e-6
        and abs(e.bounding_box().max.Z - top) < 1e-6
    )
    return polish(body, keep, chamfer_size)
