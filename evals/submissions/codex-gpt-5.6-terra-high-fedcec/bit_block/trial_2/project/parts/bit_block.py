from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5):
    """A compact bench block that stores driver bits vertically.

    shank_diameter: measured width across each bit shank; pockets add 0.3 mm clearance
    columns: number of bit pockets across the long side
    """
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    wall_thickness = 2.0
    edge_margin = 2.0
    rows = 2
    pitch = pocket_diameter + wall_thickness

    if columns < 1:
        reject("columns must be at least one", "columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", "shank_diameter")

    # There are only columns - 1 (and rows - 1) center-to-center spans.
    width = (columns - 1) * pitch + pocket_diameter + 2 * edge_margin
    depth = (rows - 1) * pitch + pocket_diameter + 2 * edge_margin
    body = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    # Cut straight, blind pockets first: their floors remain a flat 3.0 mm above bed.
    for row in range(rows):
        for column in range(columns):
            x = edge_margin + pocket_radius + column * pitch
            y = edge_margin + pocket_radius + row * pitch
            pocket = Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).translate((x, y, floor_thickness))
            body -= pocket

    # These are precisely the outer top rim and the ten pocket mouths.  Keeping the
    # bottom edges out of the selection leaves the bed perimeter sharp.
    top_edges = body.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - height) < 0.001
        and abs(edge.bounding_box().max.Z - height) < 0.001
    )
    return chamfer(top_edges, 0.8, angle=45)
