from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """A compact upright bit block.

    shank_diameter: diameter of the bit shank being stored
    columns: number of pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pitch = pocket_diameter + 2.0
    width = 2.0 * 2.0 + pocket_diameter + (columns - 1) * pitch
    depth = 2.0 * 2.0 + pocket_diameter + pitch
    height = 15.0
    floor = 3.0
    lead = 0.8

    body = Pos(width / 2.0, depth / 2.0, height / 2.0) * Box(width, depth, height)

    # Dress the blank before cutting the pockets, so only the four outside
    # perimeter edges are selected (and never the pocket rims).
    if not draft:
        blank_top_edges = body.edges().filter_by(
            lambda edge: edge.bounding_box().min.Z > height - 0.01
            and edge.bounding_box().max.Z > height - 0.01
        )
        body = chamfer(blank_top_edges, length=lead)

    for col in range(columns):
        x = 2.0 + pocket_radius + col * pitch
        for row in range(2):
            y = 2.0 + pocket_radius + row * pitch
            # Straight pocket, with its flat floor at z=3, plus the exact
            # 0.8 x 45-degree mouth lead-in from z=14.2 to the top.
            straight = Pos(x, y, floor + (height - floor - lead) / 2.0) * Cylinder(
                pocket_radius, height - floor - lead
            )
            mouth = Pos(x, y, height - lead / 2.0) * Cone(
                pocket_radius + lead, pocket_radius, lead
            )
            body = body - straight - mouth

    return body
