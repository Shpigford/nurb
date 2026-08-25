from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5):
    """Bench block with upright driver-bit pockets.

    shank_diameter: diameter of the bit shank being stored
    columns: number of pockets across the block
    """
    pocket_diameter = shank_diameter + 0.3
    pocket_radius = pocket_diameter / 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    height = floor_thickness + pocket_depth
    lead_in = 0.8
    material_between_pockets = 2.0
    outer_margin = 2.0
    rows = 2

    pitch = pocket_diameter + material_between_pockets
    width = 2.0 * outer_margin + pocket_diameter + (columns - 1) * pitch
    depth = 2.0 * outer_margin + pocket_diameter + (rows - 1) * pitch

    block = Box(
        width,
        depth,
        height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    pockets = None
    for row in range(rows):
        for column in range(columns):
            x = outer_margin + pocket_radius + column * pitch
            y = outer_margin + pocket_radius + row * pitch

            straight_pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            pockets = (
                straight_pocket if pockets is None else pockets + straight_pocket
            )

    block = block - pockets

    # Chamfer only the four top outside edges and the ten pocket mouths.  The
    # bottom perimeter, pocket floors, and pocket walls remain sharp.
    top_edges = block.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > height - 1.0e-6
    )
    return chamfer(top_edges, length=lead_in)
