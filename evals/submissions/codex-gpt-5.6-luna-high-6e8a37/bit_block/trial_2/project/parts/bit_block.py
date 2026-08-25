from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """A bench block for upright driver bits.

    shank_diameter: diameter of the bit shanks, measured across the shank
    columns: number of pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_diameter = shank_diameter + 0.3
    pitch = 8.3
    edge_margin = 2.0
    rows = 2
    floor_thickness = 3.0
    pocket_depth = 12.0
    height = floor_thickness + pocket_depth

    width = 2.0 * edge_margin + pocket_diameter + (columns - 1) * pitch
    depth = 2.0 * edge_margin + pocket_diameter + (rows - 1) * pitch

    body = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    pockets = None
    radius = pocket_diameter / 2.0
    first_x = edge_margin + radius
    first_y = edge_margin + radius
    for column in range(columns):
        for row in range(rows):
            pocket = Pos(first_x + column * pitch, first_y + row * pitch, floor_thickness) * Cylinder(
                radius, pocket_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            pockets = pocket if pockets is None else pockets + pocket

    body = body - pockets
    if draft:
        return body

    # The top perimeter and every pocket mouth are the only broken edges.
    top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > height - 1e-6
    )
    return chamfer(top_edges, length=0.8)
