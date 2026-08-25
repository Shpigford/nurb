from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """Bench block for upright driver bits.

    shank_diameter: measured diameter of the bit shanks.
    columns: number of pockets across the long side.
    """
    if columns < 1:
        reject("columns must be at least 1", "columns")
    if shank_diameter <= 0:
        reject("shank diameter must be positive", "shank_diameter")

    clearance = 0.3
    pocket_diameter = shank_diameter + clearance
    wall = 2.0
    floor = 3.0
    pocket_depth = 12.0
    height = floor + pocket_depth
    pitch = pocket_diameter + wall
    rows = 2
    width = columns * pocket_diameter + (columns - 1) * wall + 2 * wall
    depth = rows * pocket_diameter + (rows - 1) * wall + 2 * wall

    block = Box(width, depth, height)
    radius = pocket_diameter / 2
    for row in range(rows):
        for column in range(columns):
            x = -width / 2 + wall + radius + column * pitch
            y = -depth / 2 + wall + radius + row * pitch
            pocket = Cylinder(radius, pocket_depth, align=(Align.CENTER, Align.CENTER, Align.MAX)).translate((x, y, height / 2))
            block -= pocket

    # At the top plane, these are precisely the outer rim and every pocket mouth.
    top_edges = [edge for edge in block.edges() if abs(edge.bounding_box().max.Z - height / 2) < 1e-6]
    return chamfer(top_edges, 0.8)
