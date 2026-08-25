from nurb import *


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    pocket_clearance=0.3,
    pocket_depth=12.0,
    floor_thickness=3.0,
    wall_between_pockets=2.0,
    columns=5,
    rows=2,
    chamfer_size=0.8,
    draft=False,
):
    """A bench block that stands driver bits upright in a grid of round pockets.

    shank_diameter: how wide the bit shanks measure across
    pocket_clearance: extra width in each pocket so a shank drops straight in
    pocket_depth: how deep a bit sinks into the block
    floor_thickness: solid material under the pockets
    wall_between_pockets: material left between neighbouring pockets, and from the
        outer pockets to the sides of the block
    columns: how many pockets across
    rows: how many pockets deep
    chamfer_size: the lead-in bevel at each pocket mouth and around the top edge
    """
    pocket_diameter = shank_diameter + pocket_clearance

    if pocket_diameter < 2.0:
        reject(
            f"a {pocket_diameter:.2f}mm pocket is under the 2mm printable bore: "
            f"raise shank_diameter above {2.0 - pocket_clearance:.2f}",
            param="shank_diameter",
        )
    # Two chamfered mouths facing each other across the wall need more than twice the
    # chamfer of flat between them, or OCCT drops the whole pass.
    if wall_between_pockets <= 2 * chamfer_size:
        reject(
            f"a {chamfer_size}mm chamfer needs more than "
            f"{2 * chamfer_size:.2f}mm of wall to land on both sides: "
            f"raise wall_between_pockets above {2 * chamfer_size:.2f}",
            param="chamfer_size",
        )

    pitch = pocket_diameter + wall_between_pockets
    length = (columns - 1) * pitch + pocket_diameter + 2 * wall_between_pockets
    width = (rows - 1) * pitch + pocket_diameter + 2 * wall_between_pockets
    height = floor_thickness + pocket_depth

    body = Pos(0, 0, height / 2) * Box(length, width, height)

    # Pockets open straight up: a blind bore sunk from the top face, flat floor,
    # nothing over it, so the whole block prints on its own bottom without support.
    for col in range(columns):
        x = (col - (columns - 1) / 2) * pitch
        for row in range(rows):
            y = (row - (rows - 1) / 2) * pitch
            body -= Pos(x, y, height - pocket_depth / 2) * Cylinder(
                pocket_diameter / 2, pocket_depth
            )

    if draft:
        return body

    # Only what lies in the top face: the ten pocket mouths and the outer perimeter.
    # The bottom perimeter stays sharp so the block's stated size is its real size,
    # and the pocket walls stay untouched because a bit has to slide down them.
    top = body.bounding_box().max.Z
    mouths = body.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top) < 1e-6
        and abs(e.bounding_box().max.Z - top) < 1e-6
    )
    return chamfer(mouths, chamfer_size)
