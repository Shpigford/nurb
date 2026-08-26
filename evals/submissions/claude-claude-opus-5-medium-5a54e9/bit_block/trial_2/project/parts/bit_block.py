from nurb import *


@part
def bit_block(
    shank_diameter=6.0,
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
    columns: how many pockets across the long side
    rows: how many pockets across the short side
    pocket_clearance: extra width a pocket gets over the shank so bits drop in
    pocket_depth: how deep a bit sinks into its pocket
    floor_thickness: how much solid material sits under the pockets
    wall: material between neighbouring pockets, and from a pocket to the outside
    chamfer_size: the lead-in bevel at each pocket mouth and around the top edge
    """
    pocket_dia = shank_diameter + pocket_clearance
    if pocket_dia < 2.0:
        reject("a pocket under 2mm across prints closed", "shank_diameter")
    if wall <= 2 * chamfer_size:
        reject(
            "two chamfered mouths need more than 2 x chamfer_size of face between them",
            "wall",
        )

    pitch = pocket_dia + wall
    width = (columns - 1) * pitch + pocket_dia + 2 * wall
    depth = (rows - 1) * pitch + pocket_dia + 2 * wall
    height = floor_thickness + pocket_depth

    body = Pos(0, 0, height / 2) * Box(width, depth, height)

    for i in range(columns):
        for j in range(rows):
            x = (i - (columns - 1) / 2) * pitch
            y = (j - (rows - 1) / 2) * pitch
            body -= Pos(x, y, floor_thickness + pocket_depth / 2) * Cylinder(
                pocket_dia / 2, pocket_depth
            )

    if draft:
        return body

    # The top face owns exactly the edges the spec breaks: the outer perimeter and
    # the ten pocket mouths. Everything else, the bottom perimeter included, stays sharp.
    top = body.faces().filter_by(Plane.XY).sort_by(Axis.Z)[-1]
    return chamfer(top.edges(), chamfer_size)
