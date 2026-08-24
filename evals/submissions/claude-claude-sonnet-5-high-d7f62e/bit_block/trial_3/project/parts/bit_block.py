from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """
    shank_diameter: the diameter of the driver bit shanks the pockets hold
    columns: how many pocket columns run along the block's length
    """
    if columns < 1:
        reject(f"columns {columns} must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject(f"shank_diameter {shank_diameter} must be positive", param="shank_diameter")

    rows = 2
    clearance = 0.3
    pocket_dia = shank_diameter + clearance
    if pocket_dia < 2.0:
        reject(
            f"shank_diameter {shank_diameter} gives a {pocket_dia:.2f}mm pocket, "
            f"under the 2mm minimum bore: raise shank_diameter above {2.0 - clearance:.1f}",
            param="shank_diameter",
        )

    pocket_depth = 12.0
    floor = 3.0
    height = floor + pocket_depth
    wall_gap = 2.0
    edge_margin = 2.0
    pitch = pocket_dia + wall_gap
    chamfer_size = 0.8

    length = (columns - 1) * pitch + pocket_dia + 2 * edge_margin
    width = (rows - 1) * pitch + pocket_dia + 2 * edge_margin

    body = Box(length, width, height)

    x0 = -length / 2 + edge_margin + pocket_dia / 2
    y0 = -width / 2 + edge_margin + pocket_dia / 2
    pocket_z = height / 2 - pocket_depth / 2

    for c in range(columns):
        x = x0 + c * pitch
        for r in range(rows):
            y = y0 + r * pitch
            body = body - Pos(x, y, pocket_z) * Cylinder(pocket_dia / 2, pocket_depth)

    if draft:
        return body

    top_z = height / 2
    concave = set(concave_edges(body))
    top_edges = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top_z) < 1e-6
        and abs(e.bounding_box().max.Z - top_z) < 1e-6
    )
    keep = [e for e in top_edges if e not in concave]

    return chamfer(keep, chamfer_size)
