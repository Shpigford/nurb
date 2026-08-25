from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """Bench block for upright driver bits.

    shank_diameter: measured width across each bit shank
    columns: number of pockets across the long side
    """
    if shank_diameter <= 0.0:
        reject("shank_diameter must be greater than zero", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_diameter = shank_diameter + 0.3
    wall = 2.0
    pitch = pocket_diameter + wall
    rows = 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    lead_in = 0.8

    length = columns * pocket_diameter + (columns - 1) * wall + 2 * wall
    width = rows * pocket_diameter + (rows - 1) * wall + 2 * wall

    # Keep the bottom sharp and apply the requested 0.8 mm, 45-degree top rim.
    body = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    top_perimeter = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z == height
        and edge.bounding_box().max.Z == height
    )
    body = chamfer(top_perimeter, lead_in)

    # Cylindrical bores preserve the 6.3 mm shank clearance; a conical cap makes
    # the only pocket-edge break, a 0.8 mm x 45-degree lead-in at each mouth.
    bore_radius = pocket_diameter / 2
    mouth_radius = bore_radius + lead_in
    for row in range(rows):
        y = (row - (rows - 1) / 2) * pitch
        for column in range(columns):
            x = (column - (columns - 1) / 2) * pitch
            bore = Pos(x, y, floor_thickness) * Cylinder(
                bore_radius,
                pocket_depth - lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            lead = Pos(x, y, height - lead_in) * Cone(
                bore_radius,
                mouth_radius,
                lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body.cut(bore.fuse(lead))

    return body
