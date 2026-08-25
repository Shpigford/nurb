from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """A bench block with two rows of upright driver-bit pockets.

    shank_diameter: diameter of the bit shank the pockets hold
    columns: number of pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pitch = 8.3
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    block_height = floor_thickness + pocket_depth
    edge_margin = 2.0
    chamfer_size = 0.8

    width = 2.0 * edge_margin + pocket_diameter + (columns - 1) * pitch
    depth = 2.0 * edge_margin + pocket_diameter + pitch
    body = Box(width, depth, block_height, align=(Align.MIN, Align.MIN, Align.MIN))

    for column in range(columns):
        x = edge_margin + pocket_radius + column * pitch
        for row in range(2):
            y = edge_margin + pocket_radius + row * pitch
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - pocket

    if draft:
        return body

    # Only edges wholly in the top plane are selected: the four outer top edges
    # and the ten pocket mouths. The bottom perimeter remains sharp.
    top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z >= block_height - 1e-6
        and edge.bounding_box().max.Z <= block_height + 1e-6
    )
    return chamfer(top_edges, chamfer_size)
