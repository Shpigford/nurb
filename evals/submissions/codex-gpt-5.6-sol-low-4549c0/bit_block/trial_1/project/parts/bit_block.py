from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """A bench block that stores driver bits upright.

    shank_diameter: measured width across each bit's round shank
    columns: number of bit pockets in each of the two rows
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be greater than 0", param="shank_diameter")

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    wall = 2.0
    pitch = pocket_diameter + wall
    rows = 2
    width = pocket_diameter + 2 * wall + (columns - 1) * pitch
    depth = pocket_diameter + 2 * wall + (rows - 1) * pitch
    lead_in = 0.8

    body = Box(width, depth, height)

    # Break only the four top outside edges; the entire bottom perimeter remains sharp.
    top_edges = body.faces().sort_by(Axis.Z)[-1].edges()
    body = chamfer(top_edges, lead_in)

    for row in range(rows):
        for column in range(columns):
            x = -width / 2 + wall + pocket_radius + column * pitch
            y = -depth / 2 + wall + pocket_radius + row * pitch

            # A straight cylindrical pocket leaves its flat floor at z=3 exactly.
            pocket_floor = -height / 2 + floor_thickness
            pocket = Pos(x, y, pocket_floor) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

            # This frustum expands the upper 0.8 mm by 0.8 mm radially: exactly 45°.
            lead = Pos(x, y, height / 2 - lead_in) * Cone(
                pocket_radius,
                pocket_radius + lead_in,
                lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - pocket - lead

    return body
