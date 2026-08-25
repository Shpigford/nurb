from nurb import *
from build123d import Align, Box, Cylinder, Location, chamfer


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """Bench block that holds driver bits upright.

    shank_diameter: measured width across each bit shank
    columns: number of bit-pocket columns in the two-row grid
    """
    pocket_diameter = shank_diameter + 0.3
    pitch = pocket_diameter + 2.0
    side_margin = 2.0
    rows = 2
    width = columns * pocket_diameter + (columns - 1) * 2.0 + 2.0 * side_margin
    depth = rows * pocket_diameter + (rows - 1) * 2.0 + 2.0 * side_margin
    height = 15.0
    floor = 3.0

    body = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    first_x = side_margin + pocket_diameter / 2.0
    first_y = side_margin + pocket_diameter / 2.0
    for column in range(columns):
        for row in range(rows):
            pocket = Cylinder(
                pocket_diameter / 2.0,
                height - floor,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).moved(Location((first_x + column * pitch, first_y + row * pitch, floor)))
            body = body - pocket

    top_edges = [
        edge
        for edge in body.edges()
        if edge.bounding_box().min.Z == height
        and edge.bounding_box().max.Z == height
    ]
    body = chamfer(top_edges, length=0.8)

    return body
