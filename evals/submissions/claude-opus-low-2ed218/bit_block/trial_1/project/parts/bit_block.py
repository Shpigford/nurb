from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    rows=2,
    pocket_clearance=0.3,
    pocket_depth=12.0,
    floor_thickness=3.0,
    wall=2.0,
    chamfer_size=0.8,
    draft=False,
):
    """A bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: how wide the bit shanks are across
    columns: how many pockets across the long side
    rows: how many pockets across the short side
    pocket_clearance: extra width the pocket gets over the shank so bits drop in
    pocket_depth: how deep a bit sinks into the block
    floor_thickness: how much solid material sits under the pockets
    wall: material between neighbouring pockets and out to the block's sides
    chamfer_size: the lead-in break at each pocket mouth and around the top edge
    """
    if columns < 1 or rows < 1:
        reject("columns and rows must each be at least 1", param="columns")
    pocket_dia = shank_diameter + pocket_clearance
    if pocket_dia < 2.0:
        reject(
            f"shank_diameter {shank_diameter} leaves a {pocket_dia:.2f}mm pocket, "
            "under the 2mm printable bore: raise it above 1.7",
            param="shank_diameter",
        )
    if wall <= 2 * chamfer_size:
        reject(
            f"wall {wall} leaves no room for two {chamfer_size}mm chamfers to land: "
            f"raise it above {2 * chamfer_size}",
            param="wall",
        )

    pitch = pocket_dia + wall
    width = (columns - 1) * pitch + pocket_dia + 2 * wall
    depth = (rows - 1) * pitch + pocket_dia + 2 * wall
    height = floor_thickness + pocket_depth

    body = Pos(0, 0, height / 2) * Box(width, depth, height)

    for i in range(columns):
        x = (i - (columns - 1) / 2) * pitch
        for j in range(rows):
            y = (j - (rows - 1) / 2) * pitch
            body -= Pos(x, y, height - pocket_depth / 2) * Cylinder(
                pocket_dia / 2, pocket_depth
            )

    if draft:
        return body

    top = height
    lead_in = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top) < 1e-6
        and abs(e.bounding_box().max.Z - top) < 1e-6
    )
    return polish(body, lead_in, chamfer_size)
