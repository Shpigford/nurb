from nurb import *


@part
def bit_block(
    shank_diameter=6.0,
    columns=5,
    clearance=0.3,
    wall_between=2.0,
    margin=2.0,
    floor_thickness=3.0,
    pocket_depth=12.0,
    chamfer_size=0.8,
):
    """
    shank_diameter: diameter of the bits' shanks, sets each pocket's bore
    columns: how many pockets sit in a row along the block's long side
    """
    rows = 2
    pocket_dia = shank_diameter + clearance
    pitch = pocket_dia + wall_between
    width = (columns - 1) * pitch + pocket_dia + 2 * margin
    depth = (rows - 1) * pitch + pocket_dia + 2 * margin
    height = floor_thickness + pocket_depth

    body = Box(width, depth, height)

    pockets = []
    for col in range(columns):
        x = -width / 2 + margin + pocket_dia / 2 + col * pitch
        for row in range(rows):
            y = -depth / 2 + margin + pocket_dia / 2 + row * pitch
            pockets.append(
                Pos(x, y, height / 2 - pocket_depth / 2)
                * Cylinder(pocket_dia / 2, pocket_depth)
            )
    body = body - pockets

    top = height / 2
    top_edges = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top) < 1e-6
        and abs(e.bounding_box().max.Z - top) < 1e-6
    )
    pocket_edges = top_edges.filter_by(GeomType.CIRCLE)
    outer_edges = top_edges.filter_by(GeomType.LINE)

    return polish(body, pocket_edges + outer_edges, chamfer_size)
