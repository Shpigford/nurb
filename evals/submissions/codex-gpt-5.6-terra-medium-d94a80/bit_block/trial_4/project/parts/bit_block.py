from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """A compact upright holder for driver bits.

    shank_diameter: measured diameter of each bit shank
    columns: number of pockets across the long side
    """
    if shank_diameter <= 0.0:
        reject("shank_diameter must be greater than zero", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    side_material = 2.0
    between_pockets = 2.0
    floor_thickness = 3.0
    pocket_depth = 12.0
    lead_in = 0.8
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pitch = pocket_diameter + between_pockets
    rows = 2
    height = floor_thickness + pocket_depth
    length = 2.0 * side_material + pocket_diameter + (columns - 1) * pitch
    width = 2.0 * side_material + pocket_diameter + (rows - 1) * pitch

    # Chamfer the top outside rim before cutting the pockets so the bottom outline
    # stays sharp and the stated bounding box remains the functional envelope.
    block = Box(length, width, height, align=(Align.MIN, Align.MIN, Align.MIN))
    top_edges = block.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > height - 0.001
    )
    block = chamfer(top_edges, lead_in)

    bore_height = pocket_depth - lead_in
    pockets = None
    for column in range(columns):
        x = side_material + pocket_radius + column * pitch
        for row in range(rows):
            y = side_material + pocket_radius + row * pitch
            bore = Cylinder(
                pocket_radius,
                bore_height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).moved(Location((x, y, floor_thickness)))
            mouth = Cone(
                pocket_radius,
                pocket_radius + lead_in,
                lead_in,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).moved(Location((x, y, floor_thickness + bore_height)))
            cutter = bore + mouth
            pockets = cutter if pockets is None else pockets + cutter

    return block - pockets
