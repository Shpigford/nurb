from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: measured width of a bit shank
    columns: number of pockets across the block
    """
    rows = 2
    clearance = 0.3
    pocket_depth = 12.0
    wall = 2.0
    floor = 3.0
    lead_in = 0.8

    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_dia = shank_diameter + clearance
    pitch = pocket_dia + wall
    length = wall * 2 + columns * pocket_dia + (columns - 1) * wall
    width = wall * 2 + rows * pocket_dia + (rows - 1) * wall
    height = floor + pocket_depth

    body = Box(length, width, height)
    top_z = body.bounding_box().max.Z

    if not draft:
        top_outer = body.faces().sort_by(Axis.Z)[-1].outer_wire().edges()
        body = chamfer(top_outer, lead_in)

    start_x = -length / 2 + wall + pocket_dia / 2
    start_y = -width / 2 + wall + pocket_dia / 2
    z_cut = top_z - pocket_depth / 2

    for col in range(columns):
        for row in range(rows):
            x = start_x + col * pitch
            y = start_y + row * pitch
            cutter = Pos(x, y, z_cut) * Cylinder(pocket_dia / 2, pocket_depth)
            body = body - cutter

    if not draft:
        mouths = body.edges().filter_by(GeomType.CIRCLE).filter_by(
            lambda e: abs(e.center().Z - top_z) < 1e-3
        )
        body = chamfer(mouths, lead_in)

    return body
