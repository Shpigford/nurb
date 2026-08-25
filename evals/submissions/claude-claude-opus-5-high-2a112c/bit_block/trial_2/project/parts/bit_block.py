from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    rows=2,
    pocket_clearance=0.3,
    pocket_depth=12.0,
    floor_thickness=3.0,
    wall_thickness=2.0,
    chamfer_size=0.8,
    draft=False,
):
    """A bench block that stands driver bits upright in a grid of round pockets.

    shank_diameter: how wide the bit shanks measure across
    columns: how many pockets along the long side of the block
    rows: how many pockets along the short side of the block
    pocket_clearance: how much wider than the shank a pocket is, so bits drop straight in
    pocket_depth: how deep a bit sinks into the block
    floor_thickness: how much solid material sits under the pockets
    wall_thickness: how much material stands between neighbouring pockets, and from the
        outer pockets to the sides of the block
    chamfer_size: how wide the lead-in bevel around each pocket mouth is
    """
    pocket_diameter = shank_diameter + pocket_clearance

    if columns < 1 or rows < 1:
        reject("a block needs at least one pocket: raise columns above 0", param="columns")
    if pocket_diameter < 2.0:
        reject(
            f"a {pocket_diameter:.2f}mm pocket prints closed: raise shank_diameter above "
            f"{2.0 - pocket_clearance:.2f}",
            param="shank_diameter",
        )
    if wall_thickness < 2 * chamfer_size + 0.2:
        reject(
            f"wall_thickness {wall_thickness} leaves no flat between two {chamfer_size}mm "
            f"mouth chamfers: raise it above {2 * chamfer_size + 0.2:.2f}",
            param="wall_thickness",
        )
    if pocket_depth < chamfer_size + 1.0:
        reject(
            f"pocket_depth {pocket_depth} is barely deeper than its own {chamfer_size}mm "
            f"lead-in: raise it above {chamfer_size + 1.0:.2f}",
            param="pocket_depth",
        )

    # Pitch is a pocket plus one wall, so the same wall_thickness sets the material
    # between neighbours and the margin out to the sides.
    pitch = pocket_diameter + wall_thickness
    width = columns * pitch + wall_thickness
    depth = rows * pitch + wall_thickness
    height = floor_thickness + pocket_depth

    body = Box(width, depth, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for column in range(columns):
        for row in range(rows):
            x = (column - (columns - 1) / 2) * pitch
            y = (row - (rows - 1) / 2) * pitch
            body -= Pos(x, y, floor_thickness) * Cylinder(
                pocket_diameter / 2,
                pocket_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    if draft:
        return body

    # Only the edges lying in the top plane are broken: the ten pocket mouths and the
    # outer perimeter. The bottom stays sharp so the block's stated size is its real one.
    top = height
    lead_in = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top) < 1e-6
        and abs(e.bounding_box().max.Z - top) < 1e-6
    )
    return polish(body, lead_in, chamfer_size)
