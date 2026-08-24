from math import sqrt

from nurb import *

AXIS_HEIGHT = 18.0
# Gap from the pole surface: clear of the 0.1 fit, close enough for the 0.4 cradle.
CLEARANCE = 0.25
# Drop-in opening is this much wider than the pole on each side.
OPENING_EXTRA = 0.15
WALL = 3.2
LENGTH = 24.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: width across the pole; the seat follows this size.
    """
    r = pole_diameter / 2.0
    if r <= 1.0:
        reject(
            "pole_diameter is too small for a printable cradle",
            param="pole_diameter",
        )

    inner_r = r + CLEARANCE
    opening_half = r + OPENING_EXTRA
    chord = inner_r * inner_r - opening_half * opening_half
    if chord <= 0.05:
        reject(
            "pole_diameter is too small for the seat to open above the pole",
            param="pole_diameter",
        )

    drop = sqrt(chord)
    wall_top = AXIS_HEIGHT - drop
    groove_floor = AXIS_HEIGHT - inner_r
    if groove_floor < 1.2 or wall_top < 4.0:
        reject(
            "pole_diameter is too large: the pole would sit through the bed. "
            "Stay under about 32mm so the axis can stay at 18.0",
            param="pole_diameter",
        )

    width = 2.0 * (opening_half + WALL)
    body = Pos(0, 0, wall_top / 2.0) * Box(width, LENGTH, wall_top)
    pole_space = (
        Pos(0, 0, AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(inner_r, LENGTH + 4.0)
    )
    body = body - pole_space

    if draft:
        return body
    bed = body.bounding_box().min.Z
    # Chamfer only outer edges. The cradle lips and the circular rims at each end
    # must stay the pole's radius; polishing them leaves sliver faces and shortens
    # the 120 degree contact arc.
    cradle_r = inner_r + WALL * 0.4

    def outer_edge(e):
        if e.bounding_box().min.Z <= bed + 0.05:
            return False
        p = e.center()
        return p.X * p.X + (p.Z - AXIS_HEIGHT) ** 2 > cradle_r * cradle_r

    keep = body.edges().filter_by(outer_edge)
    return polish(body, keep, 1.0)
