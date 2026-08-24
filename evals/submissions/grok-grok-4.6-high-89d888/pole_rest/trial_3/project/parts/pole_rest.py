from nurb import *

# Pole axis is a bench constraint: always 18 mm above the bed, centred in X.
AXIS_HEIGHT = 18.0
# Gap to the wet finish: at least 0.1, at most 0.4 so the cradle still counts as support.
CLEARANCE = 0.2
WALL = 3.6
LENGTH = 22.0
# A little above the axis so the cylinder breaks the top face instead of kissing it.
OVERSHOOT = 0.6


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: width across the finished pole; the seat radius follows this
    """
    radius = pole_diameter / 2.0
    inner_radius = radius + CLEARANCE

    if pole_diameter < 8.0:
        reject(
            f"pole_diameter {pole_diameter} is too small to cradle on a rest this size",
            param="pole_diameter",
        )
    if inner_radius >= AXIS_HEIGHT - 1.0:
        reject(
            f"pole_diameter {pole_diameter} is too large: a seat at {AXIS_HEIGHT} mm "
            "would cut through the bed",
            param="pole_diameter",
        )

    half_width = inner_radius + WALL
    min_half = (210.0 / LENGTH) / 2.0
    half_width = max(half_width, min_half)
    width = 2.0 * half_width
    height = AXIS_HEIGHT + OVERSHOOT

    body = Box(width, LENGTH, height)
    body = body.move(Location((0, 0, height / 2.0)))

    cutter = Cylinder(inner_radius, LENGTH + 4.0)
    cutter = cutter.rotate(Axis.X, 90)
    cutter = cutter.move(Location((0, 0, AXIS_HEIGHT)))
    body = body - cutter

    if draft:
        return body
    bed = body.bounding_box().min.Z

    def outer_edge(edge):
        if edge.bounding_box().min.Z <= bed + 0.05:
            return False
        mid = edge.center()
        dist = (mid.X**2 + (mid.Z - AXIS_HEIGHT) ** 2) ** 0.5
        return dist > inner_radius + 1.0

    keep = body.edges().filter_by(outer_edge)
    return polish(body, keep, 1.0)
