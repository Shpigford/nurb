from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """A compact upright holder for driver-bit shanks.

    shank_diameter: measured width across each bit shank
    columns: number of bit pockets across the block
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0.0:
        reject("shank_diameter must be greater than zero", param="shank_diameter")

    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    pitch = 8.3
    side_wall = 2.0
    mouth_chamfer = 0.8

    width = (columns - 1) * pitch + 2.0 * (pocket_radius + side_wall)
    depth = pitch + 2.0 * (pocket_radius + side_wall)
    body = Box(width, depth, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Only the four top outside edges are chamfered; the bed perimeter remains exact.
    top_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z >= height - 1e-6
    )
    body = chamfer(top_edges, mouth_chamfer)

    pockets = None
    x0 = -((columns - 1) * pitch) / 2.0
    for column in range(columns):
        for row in range(2):
            x = x0 + column * pitch
            y = (row - 0.5) * pitch
            straight_bore = Cylinder(
                pocket_radius, pocket_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
            ).moved(Location((x, y, floor_thickness)))
            # This cone widens only the top 0.8 mm of the bore at a 45 degree angle.
            lead_in = Cone(
                pocket_radius,
                pocket_radius + mouth_chamfer,
                mouth_chamfer,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).moved(Location((x, y, height - mouth_chamfer)))
            pocket = straight_bore + lead_in
            pockets = pocket if pockets is None else pockets + pocket

    return body - pockets
