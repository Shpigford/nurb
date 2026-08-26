from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    rows=2,
    pocket_clearance=0.3,
    pocket_depth=12.0,
    wall=2.0,
    floor_thickness=3.0,
    chamfer_size=0.8,
    draft=False,
):
    """A bench block that holds driver bits shank-down in a grid of pockets.

    shank_diameter: how wide the bit shanks measure across
    columns: how many pockets across the long side
    rows: how many pockets across the short side
    pocket_clearance: how much wider than the shank each pocket is cut
    pocket_depth: how deep a bit drops into the block
    wall: material between neighbouring pockets and out to the block's sides
    floor_thickness: solid material under the pocket floors
    chamfer_size: the lead-in break at each pocket mouth and around the top
    """
    pocket_dia = shank_diameter + pocket_clearance
    if pocket_dia < 2.0:
        reject(
            f"a {pocket_dia:.1f}mm pocket is under the 2mm printable bore floor: "
            "raise shank_diameter above 1.7",
            param="shank_diameter",
        )
    if columns < 1 or rows < 1:
        reject("the grid needs at least one pocket: raise columns to 1 or more", param="columns")

    pitch = pocket_dia + wall
    width = (columns - 1) * pitch + pocket_dia + 2 * wall
    depth = (rows - 1) * pitch + pocket_dia + 2 * wall
    height = floor_thickness + pocket_depth

    body = Pos(0, 0, height / 2) * Box(width, depth, height)

    pocket = Pos(0, 0, height - pocket_depth / 2) * Cylinder(pocket_dia / 2, pocket_depth)
    for col in range(columns):
        x = (col - (columns - 1) / 2) * pitch
        for row in range(rows):
            y = (row - (rows - 1) / 2) * pitch
            body -= Pos(x, y, 0) * pocket

    if draft:
        return body

    # Only the top plane is broken: every pocket mouth gets its lead-in and the top
    # outer perimeter gets the same break. The bottom perimeter stays sharp so the
    # block's stated footprint is exact, and the pocket floors stay square.
    top = body.bounding_box().max.Z
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 1e-6 and e.bounding_box().max.Z < top + 1e-6
    )
    return polish(body, keep, chamfer_size)
