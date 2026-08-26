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
    """A bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: how wide the bit shanks measure across
    columns: how many pockets across the long side
    rows: how many pockets across the short side
    pocket_clearance: how much wider than a shank each pocket is bored
    pocket_depth: how deep a bit drops into the block
    wall: material between neighbouring pockets and out to the block sides
    floor_thickness: solid material under the pocket floors
    chamfer_size: the lead-in chamfer at each pocket mouth and around the top rim
    """
    pocket_dia = shank_diameter + pocket_clearance
    pitch = pocket_dia + wall
    width = (columns - 1) * pitch + pocket_dia + 2 * wall
    depth = (rows - 1) * pitch + pocket_dia + 2 * wall
    height = floor_thickness + pocket_depth

    # Two 0.8 chamfers meeting across a 2mm land is the kernel's `2 * size` rule with
    # room to spare; thinner and the top face vanishes between them.
    if wall <= 2 * chamfer_size:
        reject(
            f"wall {wall} leaves no top face between the {chamfer_size} pocket-mouth "
            f"chamfers: raise it above {2 * chamfer_size}",
            param="wall",
        )
    if pocket_dia <= 2 * chamfer_size:
        reject(
            f"pocket_clearance {pocket_clearance} makes a {pocket_dia}mm pocket, which "
            f"the {chamfer_size} mouth chamfer would swallow",
            param="pocket_clearance",
        )

    body = Pos(0, 0, height / 2) * Box(width, depth, height)

    x0 = -width / 2 + wall + pocket_dia / 2
    y0 = -depth / 2 + wall + pocket_dia / 2
    for i in range(columns):
        for j in range(rows):
            # Bored down from the top face, flat floor left standing on the slab.
            bore = Pos(x0 + i * pitch, y0 + j * pitch, floor_thickness) * Cylinder(
                pocket_dia / 2, pocket_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            body = body - bore

    if draft:
        return body

    # Only the top plane is broken: the pocket mouths get their lead-in and the rim
    # gets the same facet. The bottom perimeter stays sharp so the block sits flat and
    # the stated bounding box is the real one.
    top = height
    mouths = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 1e-6
    )
    return polish(body, mouths, chamfer_size)
