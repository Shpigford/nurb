from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """A compact bench block that stores two rows of driver bits upright.

    shank_diameter: measured width across each bit's round shank
    columns: number of bit pockets in each of the two rows
    """
    pocket_diameter = shank_diameter + 0.3
    material_between_pockets = 2.0
    side_material = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    chamfer_size = 0.8
    rows = 2

    if shank_diameter <= 1.7:
        reject("shank_diameter must be above 1.7mm so the pockets remain printable", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pitch = pocket_diameter + material_between_pockets
    width = columns * pocket_diameter + (columns - 1) * material_between_pockets + 2 * side_material
    depth = rows * pocket_diameter + (rows - 1) * material_between_pockets + 2 * side_material
    height = floor_thickness + pocket_depth
    body = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    for row in range(rows):
        for column in range(columns):
            x = side_material + pocket_diameter / 2 + column * pitch
            y = side_material + pocket_diameter / 2 + row * pitch
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_diameter / 2,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - pocket

    top_edges = body.edges().filter_by(
        lambda edge: abs(edge.position_at(0.25).Z - height) < 1e-6
        and abs(edge.position_at(0.75).Z - height) < 1e-6
    )
    return chamfer(top_edges, chamfer_size)
