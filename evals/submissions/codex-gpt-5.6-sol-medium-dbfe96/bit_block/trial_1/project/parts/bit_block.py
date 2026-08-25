from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
):
    """A compact bench block that stores two rows of driver bits upright.

    shank_diameter: measured width across each bit's round shank
    columns: number of bit pockets in each of the two rows
    """
    if shank_diameter <= 0.0:
        reject("shank_diameter must be greater than 0mm", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    clearance = 0.3
    pocket_depth = 12.0
    floor_thickness = 3.0
    wall_between_pockets = 2.0
    side_wall = 2.0
    chamfer_size = 0.8
    rows = 2

    pocket_diameter = shank_diameter + clearance
    pocket_radius = pocket_diameter / 2.0
    pitch = pocket_diameter + wall_between_pockets
    block_length = pocket_diameter + (columns - 1) * pitch + 2.0 * side_wall
    block_width = pocket_diameter + (rows - 1) * pitch + 2.0 * side_wall
    block_height = floor_thickness + pocket_depth

    body = Box(
        block_length,
        block_width,
        block_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Break only the four outer edges at the top; the entire bottom stays sharp.
    top_outer_edges = body.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - block_height) < 1e-6
        and abs(edge.bounding_box().max.Z - block_height) < 1e-6
    )
    body = chamfer(top_outer_edges, chamfer_size)

    first_x = -(columns - 1) * pitch / 2.0
    first_y = -(rows - 1) * pitch / 2.0

    for row in range(rows):
        for column in range(columns):
            x = first_x + column * pitch
            y = first_y + row * pitch

            # The cylinder establishes the exact 12mm depth and flat floor.
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

            # This frustum removes an exact 0.8 x 45-degree lead-in at the mouth.
            lead_in = Pos(x, y, block_height - chamfer_size) * Cone(
                pocket_radius,
                pocket_radius + chamfer_size,
                chamfer_size,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - pocket - lead_in

    return body
