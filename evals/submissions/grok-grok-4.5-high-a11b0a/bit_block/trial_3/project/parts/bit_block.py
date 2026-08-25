from nurb import *

_SHANK = float(measured("shank_diameter"))


@part
def bit_block(shank_diameter=_SHANK, columns=5, draft=False):
    """Bench block that holds driver bits upright in round pockets.

    shank_diameter: bit shank diameter the pockets are sized for
    columns: number of pockets across the long side
    """
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")
    if columns < 1:
        reject("columns must be at least 1", param="columns")

    rows = 2
    clearance = 0.3
    wall = 2.0
    pocket_depth = 12.0
    floor_thickness = 3.0
    lead_in = 0.8

    pocket_dia = shank_diameter + clearance
    pitch = pocket_dia + wall
    width = columns * pocket_dia + (columns + 1) * wall
    depth = rows * pocket_dia + (rows + 1) * wall
    height = pocket_depth + floor_thickness

    body = Box(width, depth, height)
    z_shift = height / 2 - pocket_depth / 2
    cutters = [
        loc * Pos(0, 0, z_shift) * Cylinder(pocket_dia / 2, pocket_depth)
        for loc in GridLocations(pitch, pitch, columns, rows)
    ]
    body = body - cutters

    if draft:
        return body

    # Pocket mouths and the top outer perimeter only; bottom stays sharp.
    top = body.faces().sort_by(Axis.Z)[-1]
    return chamfer(top.edges(), lead_in, angle=45)
