from nurb import *

_FIT = 0.3
_WALL = 2.0
_POCKET_DEPTH = 12.0
_FLOOR = 3.0
_LEAD_IN = 0.8
_ROWS = 2
_CUT_PAST = 1.0  # through the top face so the pocket boolean is not coplanar


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
):
    """Holds driver bits upright in a grid of round pockets.

    shank_diameter: across the bit shank; pockets are this plus 0.3 mm
    columns: pockets along the long side; two rows deep
    """
    if columns < 1:
        reject("need at least one column of bits", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_dia = shank_diameter + _FIT
    if pocket_dia < 2.0:
        reject(
            f"pockets would be {pocket_dia:.1f}mm, under the 2mm a printer can open; "
            "raise shank_diameter",
            param="shank_diameter",
        )

    pocket_r = pocket_dia / 2.0
    pitch = pocket_dia + _WALL
    height = _POCKET_DEPTH + _FLOOR
    inset = _WALL + pocket_r
    length = 2.0 * inset + (columns - 1) * pitch
    width = 2.0 * inset + (_ROWS - 1) * pitch

    body = Box(length, width, height, align=(Align.MIN, Align.MIN, Align.MIN))

    voids = None
    for col in range(columns):
        for row in range(_ROWS):
            x = inset + col * pitch
            y = inset + row * pitch
            bore = Pos(x, y, _FLOOR) * Cylinder(
                pocket_r,
                _POCKET_DEPTH + _CUT_PAST,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            voids = bore if voids is None else voids + bore
    body = body - voids

    top = body.faces().sort_by(Axis.Z)[-1]
    rims = list(top.outer_wire().edges()) + list(
        e for wire in top.inner_wires() for e in wire.edges()
    )
    return chamfer(rims, _LEAD_IN)
