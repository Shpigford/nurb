from nurb import *


@part
def bit_block(shank_diameter: float = measured("shank_diameter"), columns: int = 5):
    """A compact upright holder for driver bits.

    shank_diameter: diameter of the bits that fit the pockets
    columns: number of pockets in each row
    """
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    pitch = 8.3
    pocket_depth = 12.0
    floor = 3.0
    lead = 0.8
    width = columns * pocket_diameter + (columns - 1) * 2.0 + 4.0
    depth = 2 * pocket_diameter + 2.0 + 4.0
    height = pocket_depth + floor

    body = Pos(-width / 2, -depth / 2, 0) * Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))

    # A straight pocket with a 45-degree, 0.8 mm countersink at its mouth.
    for row in range(2):
        for column in range(columns):
            x = -((columns - 1) * pitch) / 2 + column * pitch
            y = -(pitch / 2) + row * pitch
            straight = Pos(x, y, floor) * Cylinder(pocket_radius, pocket_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
            lead_in = Pos(x, y, height - lead) * Cone(pocket_radius, pocket_radius + lead, lead, align=(Align.CENTER, Align.CENTER, Align.MIN))
            body = body - straight - lead_in

    # Only the four outside edges on the top perimeter are dressed.  Pocket
    # mouths are made explicitly above so their lead-in remains exact.
    top_edges = body.edges().filter_by(lambda edge: edge.bounding_box().min.Z > height - 0.01)
    return polish(body, top_edges, lead)
