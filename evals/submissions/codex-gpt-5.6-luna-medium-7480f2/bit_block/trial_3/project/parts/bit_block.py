from nurb import *


@part
def bit_block(
    shank_diameter: float = measured("shank_diameter"),
    columns: int = 5,
    draft=False,
):
    """A two-row bench block for upright driver bits.

    shank_diameter: diameter of the bit shanks
    columns: number of pockets in each row
    """
    if shank_diameter <= 0:
        reject("shank_diameter must be positive")
    if columns < 1:
        reject("columns must be at least one")

    pocket_diameter = shank_diameter + 0.3
    pitch = pocket_diameter + 2.0
    edge_margin = 2.0
    rows = 2
    width = 2.0 * edge_margin + pocket_diameter + (columns - 1) * pitch
    depth = 2.0 * edge_margin + pocket_diameter + (rows - 1) * pitch
    height = 15.0
    pocket_depth = 12.0
    lead_in = 0.8

    # Start with the exact-height block and chamfer only its upper perimeter.
    block = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))
    top_edges = block.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > height - 1e-6
    )
    block = chamfer(top_edges, length=lead_in)

    # The cylindrical pocket ends at the flat floor.  A separate frustum makes
    # the 0.8 x 45-degree lead-in explicit while leaving every pocket roofless.
    cutter_height = pocket_depth - lead_in
    for row in range(rows):
        for column in range(columns):
            x = edge_margin + pocket_diameter / 2.0 + column * pitch
            y = edge_margin + pocket_diameter / 2.0 + row * pitch
            bore = Pos(x, y, height - pocket_depth) * Cylinder(
                pocket_diameter / 2.0,
                cutter_height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            lead = Pos(x, y, height - lead_in) * Cone(
                pocket_diameter / 2.0,
                pocket_diameter / 2.0 + lead_in,
                lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - bore - lead

    return block
