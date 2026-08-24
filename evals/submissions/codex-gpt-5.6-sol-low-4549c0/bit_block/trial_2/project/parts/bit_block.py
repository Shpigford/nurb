from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """Bench block that stores two rows of driver bits upright.

    shank_diameter: measured width across each driver's round shank
    columns: number of bit pockets in each of the two rows
    """
    if columns < 1:
        reject("columns must be at least one", "columns")
    if shank_diameter <= 0.0:
        reject("shank diameter must be positive", "shank_diameter")

    clearance = 0.3
    wall = 2.0
    pocket_depth = 12.0
    floor = 3.0
    lead_in = 0.8
    rows = 2

    pocket_diameter = shank_diameter + clearance
    pocket_radius = pocket_diameter / 2.0
    pitch = pocket_diameter + wall
    width = pocket_diameter + 2.0 * wall + (columns - 1) * pitch
    depth = pocket_diameter + 2.0 * wall + (rows - 1) * pitch
    height = pocket_depth + floor

    block = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    # Break only the four top outside edges. The bottom perimeter remains sharp.
    top_edges = block.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - height) < 1e-7
        and abs(edge.bounding_box().max.Z - height) < 1e-7
    )
    block = chamfer(top_edges, lead_in)

    for row in range(rows):
        y = wall + pocket_radius + row * pitch
        for column in range(columns):
            x = wall + pocket_radius + column * pitch

            straight = Pos(x, y, floor) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            lead = Pos(x, y, height - lead_in) * Cone(
                pocket_radius,
                pocket_radius + lead_in,
                lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - (straight + lead)

    return block
