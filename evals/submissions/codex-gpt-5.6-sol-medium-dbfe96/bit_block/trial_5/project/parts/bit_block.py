from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """A bench block that stores driver bits upright.

    shank_diameter: measured width across each bit shank
    columns: number of pockets in each of the two rows
    """
    if shank_diameter <= 1.7:
        reject(
            "shank_diameter must be above 1.7 mm so the finished pocket is printable",
            param="shank_diameter",
        )
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    clearance = 0.3
    pocket_diameter = shank_diameter + clearance
    pocket_radius = pocket_diameter / 2
    wall_between_pockets = 2.0
    side_material = 2.0
    row_count = 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    chamfer_size = 0.8

    pitch = pocket_diameter + wall_between_pockets
    width = 2 * (side_material + pocket_radius) + (columns - 1) * pitch
    depth = 2 * (side_material + pocket_radius) + (row_count - 1) * pitch
    height = floor_thickness + pocket_depth

    body = Box(
        width,
        depth,
        height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    # Only the four horizontal edges around the top outer perimeter are broken.
    top_edges = body.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - height) < 1e-7
        and abs(edge.bounding_box().max.Z - height) < 1e-7
    )
    body = chamfer(top_edges, chamfer_size)

    first_center = side_material + pocket_radius
    straight_depth = pocket_depth - chamfer_size
    for row in range(row_count):
        y = first_center + row * pitch
        for column in range(columns):
            x = first_center + column * pitch
            straight_pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                straight_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            lead_in = Pos(x, y, height - chamfer_size) * Cone(
                pocket_radius,
                pocket_radius + chamfer_size,
                chamfer_size,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - (straight_pocket + lead_in)

    return body
