from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """A compact upright holder for driver bits.

    shank_diameter: measured width of each bit shank.
    columns: number of bit pockets across the block.
    """
    if shank_diameter <= 0.0:
        reject("shank_diameter must be greater than zero", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_diameter = shank_diameter + 0.3
    wall = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    pitch = pocket_diameter + wall
    rows = 2

    length = columns * pocket_diameter + (columns + 1) * wall
    width = rows * pocket_diameter + (rows + 1) * wall
    body = Box(length, width, height, align=(Align.MIN, Align.MIN, Align.MIN))

    pockets = None
    for row in range(rows):
        for column in range(columns):
            x = wall + pocket_diameter / 2.0 + column * pitch
            y = wall + pocket_diameter / 2.0 + row * pitch
            bore = Pos(x, y, floor_thickness) * Cylinder(
                pocket_diameter / 2.0,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            pockets = bore if pockets is None else pockets + bore

    block = body - pockets
    if draft:
        return block

    top_edges = block.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > height - 0.001
    )
    return chamfer(top_edges, 0.8)
