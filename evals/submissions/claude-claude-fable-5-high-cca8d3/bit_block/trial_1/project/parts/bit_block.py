from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, rows=2, draft=False):
    """A bench block that holds driver bits upright in round pockets.

    shank_diameter: how wide the bit shanks measure across, in mm
    columns: how many pockets along the long side
    rows: how many pockets along the short side
    """
    clearance = 0.3          # extra on the pocket so a bit drops in and stands
    wall = 2.0               # material between pockets and out to the sides
    pocket_depth = 12.0
    floor = 3.0
    lead_in = 0.8            # chamfer on pocket mouths and the top perimeter

    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if rows < 1:
        reject("rows must be at least 1", param="rows")
    if shank_diameter + clearance < 2.0:
        reject(
            "a pocket under 2mm across prints as a smear: "
            "raise shank_diameter above 1.7",
            param="shank_diameter",
        )

    pocket_dia = shank_diameter + clearance
    pitch = pocket_dia + wall
    width = (columns - 1) * pitch + pocket_dia + 2 * wall
    depth = (rows - 1) * pitch + pocket_dia + 2 * wall
    height = floor + pocket_depth

    body = Pos(0, 0, height / 2) * Box(width, depth, height)
    for i in range(columns):
        for j in range(rows):
            x = (i - (columns - 1) / 2) * pitch
            y = (j - (rows - 1) / 2) * pitch
            body -= Pos(x, y, height - pocket_depth / 2) * Cylinder(
                pocket_dia / 2, pocket_depth
            )

    if draft:
        return body

    # Every edge lying in the top plane: the pocket mouths and the outer
    # perimeter. Vertical corners and the bottom stay sharp so the bounding
    # box is exact.
    top = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - height) < 1e-6
        and abs(e.bounding_box().max.Z - height) < 1e-6
    )
    return chamfer(top, lead_in)
