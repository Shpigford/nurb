from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5):
    """A bench block for upright driver bits.

    shank_diameter: diameter of the bit shanks the pockets hold
    columns: number of pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pitch = 8.3
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    edge_margin = 2.0
    rows = 2

    width = (columns - 1) * pitch + pocket_diameter + 2.0 * edge_margin
    depth = (rows - 1) * pitch + pocket_diameter + 2.0 * edge_margin

    block = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    for column in range(columns):
        for row in range(rows):
            x = edge_margin + pocket_radius + column * pitch
            y = edge_margin + pocket_radius + row * pitch
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - pocket

    # The only broken edges are the outside top perimeter and each pocket mouth.
    # Bottom edges remain sharp so the bed contact and bounding box stay exact.
    top_edges = block.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > height - 1e-6
        and edge.bounding_box().max.Z < height + 1e-6
    )
    return chamfer(top_edges, length=0.8)
