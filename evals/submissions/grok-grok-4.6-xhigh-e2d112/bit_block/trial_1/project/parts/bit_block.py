from nurb import *


@part
def bit_block(
    shank_diameter=float(measured("shank_diameter")),
    columns=5,
    draft=False,
):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: across a bit shank; each pocket is this plus 0.3mm of clearance
    columns: how many pockets sit along the long side
    """
    clearance = 0.3
    wall = 2.0
    rows = 2
    pocket_depth = 12.0
    floor_thickness = 3.0
    lead_in = 0.8

    if columns < 1:
        reject("need at least one column of pockets", param="columns")

    pocket_dia = shank_diameter + clearance
    if pocket_dia < 2.0:
        reject(
            f"pocket diameter {pocket_dia:.2f} is under 2mm and will not print; "
            "raise shank_diameter",
            param="shank_diameter",
        )

    pitch = pocket_dia + wall
    height = pocket_depth + floor_thickness
    length = 2 * wall + (columns - 1) * pitch + pocket_dia
    width = 2 * wall + (rows - 1) * pitch + pocket_dia

    body = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pocket = Cylinder(
        pocket_dia / 2,
        pocket_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for loc in GridLocations(pitch, pitch, columns, rows):
        body -= Pos(loc.position.X, loc.position.Y, floor_thickness) * pocket

    if draft:
        return body

    top = body.faces().sort_by(Axis.Z)[-1]
    mouths = top.edges().filter_by(GeomType.CIRCLE)
    outer = top.edges().filter_by(GeomType.LINE)
    return chamfer(mouths + outer, lead_in)
