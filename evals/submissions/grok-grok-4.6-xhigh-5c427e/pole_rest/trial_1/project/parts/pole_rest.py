from nurb import *


AXIS_HEIGHT = 18.0
CLEARANCE = 0.2
WALL = 3.0
LENGTH = 22.0
SEAT_DROP = 2.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    Several stand in a row; the pole lies along Y with its axis 18mm above the bed.

    pole_diameter: across the pole; the seat follows this and keeps the axis 18mm up
    """
    if pole_diameter < 8.0:
        reject(
            f"pole_diameter {pole_diameter} is under 8mm; raise it so the cradle "
            "can still hold 120 degrees of a pole sitting at 18mm",
            param="pole_diameter",
        )

    radius = pole_diameter / 2.0
    inner_r = radius + CLEARANCE
    floor = AXIS_HEIGHT - inner_r
    if floor < WALL:
        limit = 2.0 * (AXIS_HEIGHT - WALL - CLEARANCE)
        reject(
            f"pole_diameter {pole_diameter} puts the seat {floor:.1f}mm off the bed; "
            f"keep it at or below {limit:.1f} so at least {WALL}mm of floor remains",
            param="pole_diameter",
        )

    width = 2.0 * (inner_r + WALL)
    height = AXIS_HEIGHT - SEAT_DROP

    body = Box(width, LENGTH, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cutter = Rot(90, 0, 0) * Cylinder(
        inner_r, LENGTH + 4.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    body -= Pos(0, 0, AXIS_HEIGHT) * cutter

    if draft:
        return body

    bed = body.bounding_box().min.Z
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 1e-4)
    for face in body.faces().filter_by(GeomType.CYLINDER):
        keep = keep - face.edges()
    return polish(body, keep, 1.0)
