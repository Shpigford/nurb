from nurb import *


SHANK_DIAMETER = measured("shank_diameter")


@part
def bit_block(shank_diameter=SHANK_DIAMETER, columns=5):
    """A compact bench block that stores two rows of driver bits upright.

    shank_diameter: measured width of each bit shank
    columns: number of bit pockets in each row
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0.0:
        reject("shank_diameter must be greater than 0", param="shank_diameter")

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    wall = 2.0
    pitch = pocket_diameter + wall
    rows = 2
    floor = 3.0
    pocket_depth = 12.0
    height = floor + pocket_depth
    edge_chamfer = 0.8

    width = (columns - 1) * pitch + pocket_diameter + 2.0 * wall
    depth = (rows - 1) * pitch + pocket_diameter + 2.0 * wall

    block = Box(
        width,
        depth,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    top_outer_edges = block.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - height) < 1e-7
        and abs(edge.bounding_box().max.Z - height) < 1e-7
    )
    block = chamfer(top_outer_edges, length=edge_chamfer)

    x_start = -((columns - 1) * pitch) / 2.0
    y_start = -((rows - 1) * pitch) / 2.0
    for row in range(rows):
        for column in range(columns):
            x = x_start + column * pitch
            y = y_start + row * pitch
            pocket = Pos(x, y, floor) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - pocket

    pocket_mouth_edges = block.edges().filter_by(
        lambda edge: edge.geom_type == GeomType.CIRCLE
        and abs(edge.bounding_box().min.Z - height) < 1e-7
        and abs(edge.bounding_box().max.Z - height) < 1e-7
    )
    return chamfer(pocket_mouth_edges, length=edge_chamfer)
