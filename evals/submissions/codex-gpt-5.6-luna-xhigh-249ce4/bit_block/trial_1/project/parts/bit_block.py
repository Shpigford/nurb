from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """Upright driver-bit block with a two-row grid of round pockets.

    shank_diameter: measured bit shank diameter; each pocket adds 0.3 mm.
    columns: number of pockets in each row.
    """
    rows = 2
    pitch = 8.3
    side_wall = 2.0
    floor_thickness = 3.0
    pocket_depth = 12.0
    lead_in = 0.8
    pocket_diameter = shank_diameter + 0.3
    overall_height = floor_thickness + pocket_depth

    if columns < 1:
        reject("columns must be at least 1 so the block has a pocket row", param="columns")
    if pocket_diameter < 2.0:
        reject("shank_diameter must make a pocket at least 2.0 mm across", param="shank_diameter")

    block_width = (columns - 1) * pitch + pocket_diameter + 2.0 * side_wall
    block_depth = (rows - 1) * pitch + pocket_diameter + 2.0 * side_wall

    body = Box(
        block_width,
        block_depth,
        overall_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    first_x = -block_width / 2.0 + side_wall + pocket_diameter / 2.0
    first_y = -block_depth / 2.0 + side_wall + pocket_diameter / 2.0
    pocket_radius = pocket_diameter / 2.0
    for column in range(columns):
        for row in range(rows):
            pocket = Pos(
                first_x + column * pitch,
                first_y + row * pitch,
                floor_thickness,
            ) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - pocket

    if draft:
        return body

    # Only edges lying entirely in the top plane are dressed. This includes the
    # ten pocket mouths and the four outer top edges, while leaving the bottom
    # perimeter and pocket floors sharp.
    top_edges = body.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - overall_height) < 1e-6
        and abs(edge.bounding_box().max.Z - overall_height) < 1e-6
    )
    return chamfer(top_edges, length=lead_in)
