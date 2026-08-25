from nurb import *


@part
def bit_block(
    shank_diameter=6.0,
    columns=5,
    draft=False,
):
    """Bench block for upright driver bits.

    shank_diameter: diameter of the bit shank the pockets hold
    columns: number of pockets across the block
    """
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_diameter = shank_diameter + 0.3
    pitch = 8.3
    rows = 2
    side_margin = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    lead_in = 0.8
    height = floor_thickness + pocket_depth
    width = pocket_diameter + 2.0 * side_margin + (columns - 1) * pitch
    depth = pocket_diameter + 2.0 * side_margin + (rows - 1) * pitch
    top_z = height / 2.0
    floor_z = top_z - pocket_depth

    body = Box(width, depth, height)
    for column in range(columns):
        x = -width / 2.0 + side_margin + pocket_diameter / 2.0 + column * pitch
        for row in range(rows):
            y = -depth / 2.0 + side_margin + pocket_diameter / 2.0 + row * pitch
            pocket = Pos(x, y, floor_z + pocket_depth / 2.0) * Cylinder(
                pocket_diameter / 2.0, pocket_depth
            )
            body = body - pocket

    if draft:
        return body

    # Only the top perimeter and pocket mouths are polished.  The bottom
    # perimeter remains sharp so the 15mm height and bed face stay exact.
    top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > top_z - 1e-6
    )
    return chamfer(top_edges, length=lead_in)
