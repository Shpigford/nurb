from nurb import *


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """A bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: how wide the bit shanks are, measured across
    columns: how many pockets long the block is
    """
    clearance = 0.3      # extra on each pocket over the shank, a snug drop-in
    wall = 2.0           # material between pockets and out to the sides
    pocket_depth = 12.0
    floor = 3.0          # solid material under the pocket floors
    lead_in = 0.8        # chamfer on the pocket mouths and the top perimeter
    rows = 2

    pocket_dia = shank_diameter + clearance
    if pocket_dia < 2.0:
        reject(
            f"shank_diameter {shank_diameter} makes a {pocket_dia}mm pocket, under "
            "the 2mm minimum printable hole: raise it above 1.7",
            param="shank_diameter",
        )
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    pitch = pocket_dia + wall
    length = columns * pitch + wall
    width = rows * pitch + wall
    height = floor + pocket_depth

    body = Pos(0, 0, height / 2) * Box(length, width, height)
    for i in range(columns):
        for j in range(rows):
            x = (i - (columns - 1) / 2) * pitch
            y = (j - (rows - 1) / 2) * pitch
            body -= Pos(x, y, height - pocket_depth / 2) * Cylinder(
                pocket_dia / 2, pocket_depth
            )

    if draft:
        return body
    # Exactly the edges lying in the top plane: the pocket mouths and the outer
    # perimeter. Bottom and vertical corners stay sharp so the bounding box is exact.
    top = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > height - 1e-6
    )
    return chamfer(top, lead_in)
