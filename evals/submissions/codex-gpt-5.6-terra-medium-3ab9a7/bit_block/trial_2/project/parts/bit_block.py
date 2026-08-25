from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """A compact upright holder for driver bits.

    shank_diameter: measured width across each bit shank.
    columns: number of pockets in each of the two rows.
    """
    pocket_diameter = shank_diameter + 0.3
    pocket_depth = 12.0
    floor_thickness = 3.0
    wall_thickness = 2.0
    pitch = pocket_diameter + wall_thickness
    rows = 2
    height = floor_thickness + pocket_depth

    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0.0:
        reject("shank_diameter must be positive", param="shank_diameter")

    length = columns * pocket_diameter + (columns - 1) * wall_thickness + 2 * wall_thickness
    width = rows * pocket_diameter + (rows - 1) * wall_thickness + 2 * wall_thickness
    body = Box(length, width, height, align=(Align.MIN, Align.MIN, Align.MIN))

    pockets = None
    for row in range(rows):
        for column in range(columns):
            x = wall_thickness + pocket_diameter / 2 + column * pitch
            y = wall_thickness + pocket_diameter / 2 + row * pitch
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_diameter / 2,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            pockets = pocket if pockets is None else pockets + pocket
    body = body - pockets

    if draft:
        return body

    # Exactly the top outer perimeter and the open pocket mouths: 0.8 mm at 45 degrees.
    top_edges = body.edges().filter_by(lambda edge: edge.bounding_box().min.Z > height - 0.001)
    return chamfer(top_edges, 0.8)
