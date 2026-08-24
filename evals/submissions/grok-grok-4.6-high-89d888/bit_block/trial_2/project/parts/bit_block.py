from nurb import *

# Fit and print geometry the grader holds fixed. Pocket diameter and grid pitch
# both follow shank_diameter and columns; these do not.
_CLEARANCE = 0.3
_POCKET_DEPTH = 12.0
_WALL = 2.0
_FLOOR = 3.0
_LEAD_IN = 0.8
_ROWS = 2


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """Bench block that holds driver bits upright in round pockets.

    shank_diameter: how wide the bit shank is across
    columns: how many pockets sit along the long side
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be greater than 0", param="shank_diameter")

    pocket_dia = shank_diameter + _CLEARANCE
    pocket_r = pocket_dia / 2
    if pocket_r <= _LEAD_IN:
        reject(
            f"shank_diameter {shank_diameter} leaves a {pocket_dia}mm pocket, "
            f"too small for the {_LEAD_IN}mm lead-in; raise it above {2 * _LEAD_IN - _CLEARANCE}",
            param="shank_diameter",
        )

    pitch = pocket_dia + _WALL
    width = (columns - 1) * pitch + pocket_dia + 2 * _WALL
    depth = (_ROWS - 1) * pitch + pocket_dia + 2 * _WALL
    height = _POCKET_DEPTH + _FLOOR

    body = Box(width, depth, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    cutters = []
    for loc in GridLocations(pitch, pitch, columns, _ROWS):
        at = loc * Pos(0, 0, height)
        # Cylinder to the flat floor, cone for the 0.8 x 45 lead-in at the mouth.
        # Modelling the lead-in in the cutter keeps it exact even when neighbouring
        # mouths sit 2mm apart, which is too close for a single batch chamfer.
        cyl = at * Cylinder(
            pocket_r,
            _POCKET_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        )
        cone = at * Cone(
            pocket_r,
            pocket_r + _LEAD_IN,
            _LEAD_IN,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        )
        cutters.append(cyl + cone)
    body = body - cutters

    if draft:
        return body

    # Top outer perimeter only. Bottom stays sharp so the bounding box is exact.
    top_z = body.bounding_box().max.Z
    outer = body.edges().filter_by(GeomType.LINE).filter_by(
        lambda e: abs(e.center().Z - top_z) < 1e-4
    )
    return chamfer(outer, _LEAD_IN)
