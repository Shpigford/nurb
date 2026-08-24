from nurb import *

# The pole's axis stays at this height for every diameter: the rest is used
# in a row on the bench, and a changing axis would misalign the pole.
AXIS_HEIGHT = 18.0
# Gap around the freshly finished surface. Must stay in [0.1, 0.4] so the
# pole is clear of the rest but still sitting in a close cradle.
CLEARANCE = 0.2
WALL = 3.5
LENGTH = 24.0
POLISH = 1.2


@part
def pole_rest(pole_diameter=20.0, draft=False):
    """Drying rest that cradles a freshly finished pole.

    pole_diameter: width of the pole this rest holds
    """
    if pole_diameter < 8.0:
        reject(
            f"pole_diameter {pole_diameter} is too small for a printable cradle; "
            "raise it above 8",
            param="pole_diameter",
        )

    inner_r = pole_diameter / 2.0 + CLEARANCE
    floor = AXIS_HEIGHT - inner_r
    if floor < 2.4:
        limit = 2.0 * (AXIS_HEIGHT - 2.4 - CLEARANCE)
        reject(
            f"pole_diameter {pole_diameter} puts the cradle within 2.4mm of the bed; "
            f"keep it at or below {limit:.1f}",
            param="pole_diameter",
        )

    width = 2.0 * (inner_r + WALL)
    height = AXIS_HEIGHT

    body = Pos(0, 0, height / 2.0) * Box(width, LENGTH, height)
    cutter = Pos(0, 0, AXIS_HEIGHT) * (Rot(90, 0, 0) * Cylinder(inner_r, LENGTH + 2.0))
    body = body - cutter

    if draft:
        return body

    bed = body.bounding_box().min.Z
    skip = concave_edges(body)
    keep = [
        e
        for e in body.edges()
        if e.bounding_box().max.Z > bed + 0.05 and e not in skip
    ]
    return polish(body, keep, POLISH)
