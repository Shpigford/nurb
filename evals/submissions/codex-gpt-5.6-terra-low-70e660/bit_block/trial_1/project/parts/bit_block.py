from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """A compact upright holder for driver bits.

    shank_diameter: measured width of each bit shank
    columns: number of pockets across the long side
    """
    clearance = 0.3
    wall = 2.0
    floor_thickness = 3.0
    pocket_depth = 12.0
    lead_in = 0.8

    pocket_diameter = shank_diameter + clearance
    pocket_radius = pocket_diameter / 2
    pitch = pocket_diameter + wall
    length = columns * pocket_diameter + (columns - 1) * wall + 2 * wall
    width = 2 * pocket_diameter + wall + 2 * wall

    # The upper inset makes only the top outside rim a 0.8 mm, 45-degree chamfer.
    base_height = floor_thickness + pocket_depth - lead_in
    base = Box(length, width, base_height).translate((length / 2, width / 2, base_height / 2))
    top = Box(length - 2 * lead_in, width - 2 * lead_in, lead_in).translate(
        (length / 2, width / 2, floor_thickness + pocket_depth - lead_in / 2)
    )
    block = base + top

    # Straight 12 mm bores end on the 3 mm floor; conical cutters form the lead-ins.
    pockets = None
    for row in range(2):
        for column in range(columns):
            x = wall + pocket_radius + column * pitch
            y = wall + pocket_radius + row * pitch
            bore = Cylinder(pocket_radius, pocket_depth).translate(
                (x, y, floor_thickness + pocket_depth / 2)
            )
            lead = Cone(pocket_radius + lead_in, pocket_radius, lead_in).translate(
                (x, y, floor_thickness + pocket_depth - lead_in / 2)
            )
            cutter = bore + lead
            pockets = cutter if pockets is None else pockets + cutter

    return block - pockets
