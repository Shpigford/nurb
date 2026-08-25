from nurb import *

# Fixed layout: two rows deep. Columns and shank size drive the rest.
_ROWS = 2
_CLEARANCE = 0.3
_WALL = 2.0
_MARGIN = 2.0
_POCKET_DEPTH = 12.0
_FLOOR = 3.0
_LEAD = 0.8


@part
def bit_block(shank_diameter=measured("shank_diameter"), columns=5, draft=False):
    """Bench block that holds driver bits upright in a grid of round pockets.

    shank_diameter: bit shank width across; pockets are this plus 0.3 clearance
    columns: number of pockets across the long side (two rows deep)
    """
    if columns < 1:
        reject("columns must be at least 1", param="columns")
    if shank_diameter <= 0:
        reject("shank_diameter must be positive", param="shank_diameter")

    pocket_dia = shank_diameter + _CLEARANCE
    pocket_r = pocket_dia / 2.0
    pitch = pocket_dia + _WALL
    length = (columns - 1) * pitch + pocket_dia + 2.0 * _MARGIN
    width = (_ROWS - 1) * pitch + pocket_dia + 2.0 * _MARGIN
    height = _POCKET_DEPTH + _FLOOR

    body = Box(length, width, height)

    for loc in GridLocations(pitch, pitch, columns, _ROWS):
        # Cutter pokes 0.01 above the top so the boolean is clean; floor sits at
        # exactly pocket_depth below the top face.
        top = loc * Pos(0, 0, height / 2.0 + 0.01)
        body = body - top * Cylinder(
            pocket_r,
            _POCKET_DEPTH + 0.01,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        )

    if draft:
        return body

    # Pocket mouths first: exact 0.8 x 45° lead-in on each circular rim.
    # Then the top outer perimeter, same size. Bottom and vertical corners stay
    # sharp so the bounding box remains exact. Sequential chamfers (re-selected
    # on the updated solid) land where a single combined call would not.
    top_z = body.bounding_box().max.Z
    mouths = body.edges().filter_by(
        lambda e: (
            e.geom_type == GeomType.CIRCLE
            and abs(e.bounding_box().center().Z - top_z) < 1e-3
        )
    )
    body = chamfer(mouths, _LEAD)

    top_z = body.bounding_box().max.Z
    outer = body.edges().filter_by(
        lambda e: (
            e.geom_type == GeomType.LINE
            and abs(e.bounding_box().max.Z - top_z) < 1e-3
            and abs(e.bounding_box().min.Z - top_z) < 1e-3
        )
    )
    return chamfer(outer, _LEAD)
