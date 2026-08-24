from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """A compact upright holder for driver bits.

    shank_diameter: measured width of a bit shank
    columns: number of pockets across the block
    """
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    edge_wall = 2.0
    pitch = pocket_diameter + 2.0
    rows = 2

    length = 2 * (edge_wall + pocket_radius) + (columns - 1) * pitch
    width = 2 * (edge_wall + pocket_radius) + (rows - 1) * pitch
    height = floor_thickness + pocket_depth

    block = Box(length, width, height)
    for row in range(rows):
        for column in range(columns):
            x = -length / 2 + edge_wall + pocket_radius + column * pitch
            y = -width / 2 + edge_wall + pocket_radius + row * pitch
            pocket = Cylinder(pocket_radius, pocket_depth).translate((x, y, floor_thickness))
            block = block.cut(pocket)

    # Only horizontal edges at the top are eased: the rim and each pocket mouth.
    top = block.bounding_box().max.Z
    top_edges = block.edges().filter_by(lambda edge: edge.bounding_box().min.Z == top)
    return polish(block, top_edges, 0.8)
