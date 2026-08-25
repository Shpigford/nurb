from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """Bench block for upright driver bits.

    shank_diameter: diameter of the bit shanks
    columns: number of pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pitch = 8.3
    margin = 2.0
    pocket_diameter = shank_diameter + 0.3
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    rows = 2

    width = 2.0 * margin + pocket_diameter + pitch * (columns - 1)
    depth = 2.0 * margin + pocket_diameter + pitch * (rows - 1)

    block = Pos(0, 0, height / 2.0) * Box(width, depth, height)

    pockets = None
    for column in range(columns):
        x = -width / 2.0 + margin + pocket_diameter / 2.0 + pitch * column
        for row in range(rows):
            y = -depth / 2.0 + margin + pocket_diameter / 2.0 + pitch * row
            bore_radius = pocket_diameter / 2.0
            lead_in = Pos(x, y, height - 0.8 / 2.0) * Cone(
                bore_radius, bore_radius + 0.8, 0.8
            )
            pocket = Pos(x, y, floor_thickness + (pocket_depth - 0.8) / 2.0) * Cylinder(
                bore_radius, pocket_depth - 0.8
            )
            pocket = pocket + lead_in
            pockets = pocket if pockets is None else pockets + pocket

    block = block - pockets

    top_edges = block.edges().filter_by(
        lambda edge: (
            edge.bounding_box().min.Z > height - 1e-6
            and max(
                edge.bounding_box().max.X - edge.bounding_box().min.X,
                edge.bounding_box().max.Y - edge.bounding_box().min.Y,
            )
            > pocket_diameter + 2.0
        )
    )
    return polish(block, top_edges, 0.8)
