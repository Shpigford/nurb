from nurb import *


@part
def bit_block(
    shank_diameter: float = measured("shank_diameter"),
    columns: int = 5,
):
    """A compact, flat-bottomed bench block for upright driver bits.

    shank_diameter: measured diameter of the bit shanks
    columns: number of pockets across the long direction
    """
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    wall = 2.0
    pocket_depth = 12.0
    floor = 3.0
    height = floor + pocket_depth
    pitch = pocket_diameter + wall
    length = 2 * (pocket_radius + wall) + (columns - 1) * pitch
    width = 2 * (pocket_radius + wall) + pitch

    block = Box(length, width, height, align=(Align.MIN, Align.MIN, Align.MIN))

    pockets = []
    for row in range(2):
        for column in range(columns):
            x = wall + pocket_radius + column * pitch
            y = wall + pocket_radius + row * pitch
            pockets.append(
                Cylinder(
                    pocket_radius,
                    pocket_depth,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                ).translate((x, y, height))
            )
    for pocket in pockets:
        block = block.cut(pocket)

    # Only rim edges at the top: the outside perimeter and every pocket mouth.
    top_edges = [edge for edge in block.edges() if abs(edge.center().Z - height) < 0.001]
    return chamfer(top_edges, 0.8)
