from nurb import *


@part
def bit_block(shank_diameter: float = 6.0, columns: int = 5):
    """A compact bench block that holds two rows of driver bits upright.

    shank_diameter: measured width of each driver's round shank
    columns: number of bit pockets in each of the two rows
    """
    pocket_clearance = 0.3
    wall_between_pockets = 2.0
    side_wall = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    lead_in = 0.8
    rows = 2

    pocket_diameter = shank_diameter + pocket_clearance
    pocket_radius = pocket_diameter / 2
    pitch = pocket_diameter + wall_between_pockets
    width = pocket_diameter + (columns - 1) * pitch + 2 * side_wall
    depth = pocket_diameter + (rows - 1) * pitch + 2 * side_wall
    height = floor_thickness + pocket_depth

    block = Box(
        width,
        depth,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    first_x = -(columns - 1) * pitch / 2
    first_y = -(rows - 1) * pitch / 2
    for row in range(rows):
        for column in range(columns):
            x = first_x + column * pitch
            y = first_y + row * pitch
            pocket = Pos(x, y, floor_thickness) * Cylinder(
                pocket_radius,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            block = block - pocket

    # All and only the edges lying wholly in the top plane are the outer top
    # perimeter and the pocket mouths. Chamfering this set leaves every floor
    # edge and the block's bottom perimeter sharp.
    top_edges = block.edges().filter_by(
        lambda edge: abs(edge.bounding_box().min.Z - height) < 1e-7
        and abs(edge.bounding_box().max.Z - height) < 1e-7
    )
    return chamfer(top_edges, lead_in)
