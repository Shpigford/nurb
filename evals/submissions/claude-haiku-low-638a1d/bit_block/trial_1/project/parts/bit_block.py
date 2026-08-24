from nurb import *

@part
def bit_block(shank_diameter=6.0, columns=5):
    """Bench block holding driver bits upright.

    shank_diameter: bit shank diameter in mm
    columns: number of pocket columns
    """

    # Pocket dimensions
    pocket_diameter = shank_diameter + 0.3
    pocket_depth = 12.0
    total_height = 15.0

    # Grid spacing and margins
    grid_pitch = 8.3
    edge_margin = 2.0

    # Rows: fixed at 2 rows as per requirements
    rows = 2

    # Block dimensions
    width = edge_margin * 2 + pocket_diameter + (columns - 1) * grid_pitch
    depth = edge_margin * 2 + pocket_diameter + (rows - 1) * grid_pitch
    height = total_height

    # Create base block using BuildPart
    with BuildPart() as bp:
        Box(width, depth, height)

    block = bp.part

    # Remove pockets by subtracting cylinders
    for col in range(columns):
        for row in range(rows):
            # Pocket center coordinates (relative to block center)
            x = -width / 2 + edge_margin + pocket_diameter / 2 + col * grid_pitch
            y = -depth / 2 + edge_margin + pocket_diameter / 2 + row * grid_pitch
            z = height / 2 - pocket_depth

            # Create pocket cylinder
            with BuildPart() as bp_pocket:
                with Locations(Location(Vector(x, y, z))):
                    Cylinder(pocket_diameter / 2, pocket_depth)
            pocket = bp_pocket.part
            block = block - pocket

    # Chamfer all top edges (pocket mouths + outer perimeter) with 0.8mm x 45 degree
    top_edges = [e for e in block.edges() if e.center().Z > height / 2 - 0.1]
    if top_edges:
        block = chamfer(top_edges, 0.8)

    return block
