from nurb import *

# Fit clearance on the measured shank, and the wall the grid is built from.
_CLEARANCE = 0.3
_WALL = 2.0
_POCKET_DEPTH = 12.0
_FLOOR = 3.0
_LEAD_IN = 0.8
_ROWS = 2
_SEATED = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def bit_block(
    shank_diameter=float(measured("shank_diameter")),
    columns=5,
    draft=False,
):
    """Hold driver bits upright in a bench block.

    shank_diameter: bit shank width; pockets are this plus 0.3mm of clearance
    columns: number of bit pockets along the long side
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be greater than 0", param="shank_diameter")

    pocket_dia = shank_diameter + _CLEARANCE
    pocket_r = pocket_dia / 2
    pitch = pocket_dia + _WALL
    margin = _WALL + pocket_r
    width = 2 * margin + (columns - 1) * pitch
    depth = 2 * margin + (_ROWS - 1) * pitch
    height = _POCKET_DEPTH + _FLOOR

    # Vertical sides and a sharp bed face; the 0.8mm top rim is lofted on so the
    # corner is a miter rather than a sliver triangle from chamfer().
    base = Box(width, depth, height - _LEAD_IN, align=_SEATED)
    cap = loft(
        [
            Pos(0, 0, height - _LEAD_IN) * Face.make_rect(width, depth),
            Pos(0, 0, height) * Face.make_rect(width - 2 * _LEAD_IN, depth - 2 * _LEAD_IN),
        ],
        ruled=True,
    )
    body = base + cap

    extra = 1.0
    cutter = None
    for col in range(columns):
        for row in range(_ROWS):
            x = -width / 2 + margin + col * pitch
            y = -depth / 2 + margin + row * pitch
            # Cylinder through the top so the mouth is open; cone is the 0.8 x 45
            # lead-in and overshoots the top face so the boolean is not coplanar.
            shaft = Pos(x, y, _FLOOR) * Cylinder(
                pocket_r, _POCKET_DEPTH + extra, align=_SEATED
            )
            cone = Pos(x, y, height - _LEAD_IN) * Cone(
                pocket_r,
                pocket_r + _LEAD_IN + extra,
                _LEAD_IN + extra,
                align=_SEATED,
            )
            bit = shaft + cone
            cutter = bit if cutter is None else cutter + bit
    body = body - cutter

    # Lead-ins are functional, not polish; draft does not drop them.
    return body
