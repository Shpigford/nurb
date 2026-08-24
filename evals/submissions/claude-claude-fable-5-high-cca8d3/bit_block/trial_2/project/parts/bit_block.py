from nurb import *


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """A bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: how wide the bit shanks are, measured across
    columns: how many pockets long the block is
    """
    wall = 2.0  # material between pocket walls, and from pockets to the sides
    pocket_diameter = shank_diameter + 0.3  # free-ish drop-in fit for the shank
    pocket_depth = 12.0
    floor = 3.0
    rows = 2
    lead_in = 0.8

    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if pocket_diameter < 2.0:
        reject(
            f"a {pocket_diameter:.1f}mm pocket is under the 2mm minimum printable "
            "hole: raise shank_diameter above 1.7",
            param="shank_diameter",
        )

    pitch = pocket_diameter + wall
    block_x = columns * pitch + wall
    block_y = rows * pitch + wall
    height = floor + pocket_depth

    body = Pos(0, 0, height / 2) * Box(block_x, block_y, height)
    for i in range(columns):
        for j in range(rows):
            x = (i - (columns - 1) / 2) * pitch
            y = (j - (rows - 1) / 2) * pitch
            body -= Pos(x, y, height - pocket_depth / 2) * Cylinder(
                pocket_diameter / 2, pocket_depth
            )

    if draft:
        return body

    # Chamfer only what lies in the top plane: the pocket mouths and the top outer
    # perimeter. Vertical corners and the bottom stay sharp so the footprint is exact.
    top = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > height - 1e-6
    )
    return polish(body, top, lead_in)
