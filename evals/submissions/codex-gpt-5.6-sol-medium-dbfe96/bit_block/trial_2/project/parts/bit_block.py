from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """A compact bench block that holds two rows of driver bits upright.

    shank_diameter: measured diameter across each bit shank
    columns: number of bit pockets in each of the two rows
    """
    clearance = 0.3
    wall = 2.0
    rows = 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    lead_in = 0.8

    if shank_diameter <= 0:
        raise ValueError("shank_diameter must be positive")
    if columns < 1:
        raise ValueError("columns must be at least 1")

    pocket_diameter = shank_diameter + clearance
    pitch = pocket_diameter + wall
    width = columns * pocket_diameter + (columns + 1) * wall
    depth = rows * pocket_diameter + (rows + 1) * wall
    height = pocket_depth + floor_thickness

    body = Box(
        width,
        depth,
        height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    first_center = wall + pocket_diameter / 2
    for row in range(rows):
        for column in range(columns):
            x = first_center + column * pitch
            y = first_center + row * pitch
            cutter = Pos(x, y, floor_thickness) * Cylinder(
                pocket_diameter / 2,
                pocket_depth + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body = body - cutter

    # These are exactly the four outer top edges and every circular pocket mouth.
    # Chamfering only this set leaves the entire bottom perimeter sharp.
    top_edges = body.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - height) < 1e-6
        and abs(edge.bounding_box().max.Z - height) < 1e-6
    )
    return chamfer(top_edges, lead_in)
