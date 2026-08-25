from math import cos, radians, sin

from nurb import *

AXIS_HEIGHT = 18.0
CLEARANCE = 0.2
WRAP_HALF_DEG = 80.0
TOP_WALL = 4.5
LENGTH = 22.0
MIN_FLOOR = 2.5


@part
def pole_rest(pole_diameter=float(measured("pole_diameter")), draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: width of the pole across
    """
    inner_r = pole_diameter / 2.0 + CLEARANCE
    floor = AXIS_HEIGHT - inner_r
    if floor < MIN_FLOOR:
        limit = 2.0 * (AXIS_HEIGHT - MIN_FLOOR - CLEARANCE)
        reject(
            f"pole_diameter {pole_diameter} is too large to cradle on an "
            f"{AXIS_HEIGHT:.0f}mm-high axis with a printable floor; "
            f"lower it below {limit:.1f}",
            param="pole_diameter",
        )
    if pole_diameter < 8.0:
        reject(
            f"pole_diameter {pole_diameter} is too small for a 120-degree "
            "cradle; raise it above 8",
            param="pole_diameter",
        )

    half = radians(WRAP_HALF_DEG)
    height = AXIS_HEIGHT - inner_r * cos(half)
    width = 2.0 * (inner_r * sin(half) + TOP_WALL)

    body = Location((0, 0, height / 2.0)) * Box(width, LENGTH, height)
    void = Location((0, 0, AXIS_HEIGHT), (90, 0, 0)) * Cylinder(
        inner_r, LENGTH + 4.0
    )
    body = body - void

    if draft:
        return body
    bed = body.bounding_box().min.Z
    groove = body.faces().filter_by(GeomType.CYLINDER).edges()
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-4 and e not in groove
    )
    return polish(body, keep, 1.0)
