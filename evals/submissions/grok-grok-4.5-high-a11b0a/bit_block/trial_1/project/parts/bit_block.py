from nurb import *

# Fit clearance past the measured shank, and the fixed feature sizes.
_CLEARANCE = 0.3
_POCKET_DEPTH = 12.0
_FLOOR = 3.0
_MARGIN = 2.0
_GAP = 2.0
_LEAD = 0.8
_ROWS = 2


@part
def bit_block(shank_diameter=6.0, columns=5, draft=False):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: across-flat of the bit shank the pockets are sized for
    columns: number of pockets along the long side (rows stay at 2)
    """
    columns = int(columns)
    if columns < 1:
        reject("need at least one column of pockets", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_dia = shank_diameter + _CLEARANCE
    pitch = pocket_dia + _GAP
    width = 2 * _MARGIN + pocket_dia + (columns - 1) * pitch
    depth = 2 * _MARGIN + pocket_dia + (_ROWS - 1) * pitch
    height = _POCKET_DEPTH + _FLOOR

    body = Box(width, depth, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    radius = pocket_dia / 2
    x0 = -width / 2 + _MARGIN + radius
    y0 = -depth / 2 + _MARGIN + radius
    cut = None
    for col in range(columns):
        for row in range(_ROWS):
            x = x0 + col * pitch
            y = y0 + row * pitch
            cyl = Pos(x, y, height) * Cylinder(
                radius, _POCKET_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MAX)
            )
            cut = cyl if cut is None else cut + cyl
    body = body - cut

    if draft:
        return body

    # Only the pocket mouths and the top outer perimeter get the 0.8 x 45° lead-in.
    # Bottom perimeter and vertical corners stay sharp so the bounding box is exact.
    top = body.faces().sort_by(Axis.Z)[-1]
    mouths = top.edges().filter_by(GeomType.CIRCLE)
    outer = top.edges().filter_by(GeomType.LINE)
    return chamfer(list(mouths) + list(outer), _LEAD)
