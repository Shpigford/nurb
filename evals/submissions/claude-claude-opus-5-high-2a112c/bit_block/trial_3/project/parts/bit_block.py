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

    shank_diameter: how wide the bit shanks measure across
    columns: how many pockets run left to right
    rows: how many pockets run front to back
    pocket_clearance: how much wider than a shank each pocket is cut, so bits drop in
    pocket_depth: how deep a bit sinks into the block
    floor_thickness: how much solid material sits under the pockets
    wall: how much material stands between neighbouring pockets, and around the outside
    chamfer_size: how big the lead-in chamfer at each pocket mouth is
    """
    if columns < 1 or rows < 1:
        reject(
            "a block needs at least one pocket in each direction",
            param="columns" if columns < 1 else "rows",
        )
    pocket_diameter = shank_diameter + pocket_clearance
    if pocket_diameter < 2.0:
        reject(
            f"a {pocket_diameter:.2f}mm pocket prints as a smear: "
            f"raise shank_diameter above {2.0 - pocket_clearance:.2f}",
            param="shank_diameter",
        )
    # Two chamfered mouths need more than 2 * chamfer_size of face between them, and a
    # wall thinner than that also stops being a printable wall.
    if wall <= 2 * chamfer_size:
        reject(
            f"a {wall}mm wall cannot carry two {chamfer_size}mm chamfers: "
            f"raise wall above {2 * chamfer_size}",
            param="wall",
        )

    pitch = pocket_diameter + wall
    width = (columns - 1) * pitch + pocket_diameter + 2 * wall
    depth = (rows - 1) * pitch + pocket_diameter + 2 * wall
    height = pocket_depth + floor_thickness

    body = Box(width, depth, height)
    top = height / 2

    for i in range(columns):
        x = (i - (columns - 1) / 2) * pitch
        for j in range(rows):
            y = (j - (rows - 1) / 2) * pitch
            body -= Pos(x, y, top - pocket_depth / 2) * Cylinder(
                pocket_diameter / 2, pocket_depth
            )

    if draft:
        return body

    # Only the edges lying in the top plane: the outer perimeter and the ten pocket
    # mouths. The bottom perimeter stays sharp so the bounding box is the stated one,
    # and the pocket floors are concave, which polish never touches.
    eps = 1e-6
    mouths = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - eps
    )
    return polish(body, mouths, chamfer_size)
