from nurb import *


@part
def bit_block(shank_diameter: float = measured("shank_diameter"), columns: int = 5):
    """A flat bench block that stores driver bits upright.

    shank_diameter: diameter of the bit shanks held by the pockets
    columns: number of pockets across the long side
    """
    if shank_diameter <= 0:
        reject("The bit shank diameter must be positive.", "shank_diameter")
    if columns < 1:
        reject("At least one column is required.", "columns")

    clearance = 0.3
    pocket_diameter = shank_diameter + clearance
    pocket_radius = pocket_diameter / 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    edge_wall = 2.0
    pitch = 8.3
    rows = 2

    width = 2 * edge_wall + pocket_diameter + (columns - 1) * pitch
    depth = 2 * edge_wall + pocket_diameter + (rows - 1) * pitch
    block = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    for row in range(rows):
        for column in range(columns):
            x = edge_wall + pocket_radius + column * pitch
            y = edge_wall + pocket_radius + row * pitch
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block -= pocket

    # Break only the circular pocket mouths, then the four top exterior edges.
    pocket_mouths = block.edges().filter_by(GeomType.CIRCLE).filter_by_position(
        Axis.Z, height - 0.01, height + 0.01
    )
    block = chamfer(pocket_mouths, 0.8, 0.8)
    top_perimeter = block.edges().filter_by(GeomType.LINE).filter_by_position(
        Axis.Z, height - 0.01, height + 0.01
    )
    return chamfer(top_perimeter, 0.8, 0.8)
