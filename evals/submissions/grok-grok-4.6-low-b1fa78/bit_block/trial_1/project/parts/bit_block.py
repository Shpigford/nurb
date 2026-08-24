from nurb import *

_CLEARANCE = 0.3
_WALL = 2.0
_ROWS = 2
_POCKET_DEPTH = 12.0
_FLOOR = 3.0
_LEAD = 0.8


@part
def bit_block(
    shank_diameter=measured("shank_diameter"),
    columns=5,
    draft=False,
):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: bit shank across, pockets are this plus 0.3
    columns: how many pockets across the long side
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter < 1.0:
        reject("shank_diameter is too small to print a pocket", param="shank_diameter")

    pocket_d = shank_diameter + _CLEARANCE
    pitch = pocket_d + _WALL
    block_x = 2 * _WALL + columns * pocket_d + (columns - 1) * _WALL
    block_y = 2 * _WALL + _ROWS * pocket_d + (_ROWS - 1) * _WALL
    height = _POCKET_DEPTH + _FLOOR

    body = Box(block_x, block_y, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    origin_x = -block_x / 2 + _WALL + pocket_d / 2
    origin_y = -block_y / 2 + _WALL + pocket_d / 2
    cuts = []
    for col in range(columns):
        for row in range(_ROWS):
            x = origin_x + col * pitch
            y = origin_y + row * pitch
            # Overshoot the top face so the pocket is open, floor at height - 12.
            cuts.append(
                Cylinder(
                    pocket_d / 2,
                    _POCKET_DEPTH + 0.2,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                ).move(Location((x, y, height + 0.2)))
            )
    body -= cuts

    if draft:
        return body

    top_z = height
    mouths = body.edges().filter_by(GeomType.CIRCLE).filter_by(
        lambda e: abs(e.center().Z - top_z) < 1e-3
    )
    outer_top = (
        body.faces()
        .filter_by(Axis.Z)
        .sort_by(Axis.Z)[-1]
        .edges()
        .filter_by(GeomType.LINE)
    )
    return chamfer(mouths + outer_top, _LEAD)
