from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
):
    """Bench block for upright driver bits.

    shank_diameter: diameter of the bit shanks held by the pockets
    columns: number of pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be greater than 0", param="shank_diameter")

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pitch = 8.3
    side_margin = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    block_height = floor_thickness + pocket_depth
    lead_in = 0.8

    # The two rows and the side margins stay fixed as the pocket diameter
    # changes; the width also expands or contracts with the column count.
    block_width = 2.0 * side_margin + (columns - 1) * pitch + pocket_diameter
    block_depth = 2.0 * side_margin + pitch + pocket_diameter

    block = Box(
        block_width,
        block_depth,
        block_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Only the four upper outside edges are chamfered.  The bottom perimeter
    # remains sharp so the stated footprint and bed contact stay exact.
    upper_edges = block.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > block_height - 1e-6
    )
    block = chamfer(upper_edges, length=lead_in)

    x_positions = [
        (index - (columns - 1) / 2.0) * pitch for index in range(columns)
    ]
    y_positions = (-pitch / 2.0, pitch / 2.0)

    # The cylindrical portion reaches the flat floor.  The short conical
    # subtraction is the exact 0.8 x 45-degree mouth lead-in.
    straight_depth = pocket_depth - lead_in
    for x in x_positions:
        for y in y_positions:
            straight_pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                straight_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            mouth_lead_in = Pos(x, y, floor_thickness + straight_depth) * Cone(
                pocket_radius,
                pocket_radius + lead_in,
                lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - straight_pocket
            block = block - mouth_lead_in

    return block
