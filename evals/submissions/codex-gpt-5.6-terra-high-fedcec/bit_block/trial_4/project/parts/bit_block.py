from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5):
    """A compact upright holder for driver bits.

    shank_diameter: measured width across each bit's shank
    columns: number of pockets along the long side
    """
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2
    wall = 2.0
    rows = 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    pitch = pocket_diameter + wall

    width = columns * pocket_diameter + (columns - 1) * wall + 2 * wall
    depth = rows * pocket_diameter + (rows - 1) * wall + 2 * wall
    body = Box(width, depth, height)
    top = body.bounding_box().max.Z
    top_perimeter = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > top - 0.01
    )
    # Keep the bed perimeter sharp; this is deliberately the four upper outer edges.
    body = polish(body, top_perimeter, 0.8)

    # The primitives are centred on all axes.  The straight bore therefore spans
    # from the top of the 3 mm floor to the top face, and the cone cuts its mouth.
    x0 = -width / 2 + wall + pocket_radius
    y0 = -depth / 2 + wall + pocket_radius
    pockets = None
    for row in range(rows):
        for column in range(columns):
            center_x = x0 + column * pitch
            center_y = y0 + row * pitch
            bore = Cylinder(pocket_radius, pocket_depth).translate(
                (
                    center_x,
                    center_y,
                    body.bounding_box().min.Z + floor_thickness + pocket_depth / 2,
                )
            )
            lead_in = Cone(pocket_radius, pocket_radius + 0.8, 0.8).translate(
                (center_x, center_y, top - 0.4)
            )
            pocket = bore.fuse(lead_in)
            pockets = pocket if pockets is None else pockets.fuse(pocket)

    return body.cut(pockets)
