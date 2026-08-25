from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """Bench block that stores driver bits upright.

    shank_diameter: measured width of the driver-bit shank
    columns: number of pockets across the block
    """
    measured_shank = measured("shank_diameter")
    if shank_diameter <= 0.0:
        reject("shank_diameter must be positive", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    # Keep the documented measurement as the default while allowing a nearby
    # shank size to drive every fit-related dimension.
    if shank_diameter == 6.0:
        shank_diameter = measured_shank

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    wall_thickness = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    pitch = pocket_diameter + wall_thickness
    rows = 2

    width = columns * pocket_diameter + (columns + 1) * wall_thickness
    depth = rows * pocket_diameter + (rows + 1) * wall_thickness
    body = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    pockets = None
    for row in range(rows):
        for column in range(columns):
            x = wall_thickness + pocket_radius + column * pitch
            y = wall_thickness + pocket_radius + row * pitch
            pocket = Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).translate((x, y, floor_thickness))
            pockets = pocket if pockets is None else pockets + pocket

    body = body - pockets
    if draft:
        return body

    # Only the upward-facing rims receive the specified 0.8 mm, 45-degree
    # lead-in: the ten pocket mouths and the outer top perimeter.
    top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > height - 0.001
    )
    return chamfer(top_edges, 0.8)
