from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """A bench block for storing driver bits upright.

    shank_diameter: diameter of the bit shanks the pockets receive
    columns: number of pockets across the block
    """
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pitch = pocket_diameter + 2.0
    outer_wall = 2.0
    row_count = 2
    height = 15.0
    pocket_depth = 12.0
    floor = height - pocket_depth
    lead_in = 0.8

    width = 2.0 * outer_wall + columns * pocket_diameter + (columns - 1) * 2.0
    depth = 2.0 * outer_wall + row_count * pocket_diameter + (row_count - 1) * 2.0

    block = Box(
        width,
        depth,
        height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    # Only the top outer perimeter is chamfered.  In particular, the bottom
    # perimeter remains sharp so the nominal bounding box stays exact.
    top_edges = block.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > height - 1e-6
    )
    block = chamfer(top_edges, length=lead_in)

    for column in range(columns):
        x = outer_wall + pocket_radius + column * pitch
        for row in range(row_count):
            y = outer_wall + pocket_radius + row * pitch

            # The straight pocket ends on a flat floor at z=3.0.
            bore = Pos(x, y, floor) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - bore

            # A 0.8mm x 45-degree lead-in grows the mouth by 0.8mm radially.
            lead = Pos(x, y, height - lead_in) * Cone(
                pocket_radius,
                pocket_radius + lead_in,
                lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - lead

    return block
