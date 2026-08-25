from math import cos, radians, sqrt

from nurb import *

# Pole axis is fixed in the rest's print orientation: along Y, 18 mm above the bed,
# centered on the footprint in X. Nearby pole sizes rebuild around this axis.
AXIS_HEIGHT = 18.0
# Gap to the finished surface: above 0.1 so nothing touches, under 0.4 so the
# cradle still counts as support rather than a distant wall.
CLEARANCE = 0.25
# Extra material beside the groove at the top face, after the 1 mm polish.
SIDE_WALL = 3.2
# Long enough that two-thirds of Y is still a full cradle after end chamfers.
REST_LENGTH = 22.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while it dries.

    pole_diameter: across the pole this rest holds
    """
    inner_r = pole_diameter / 2.0 + CLEARANCE
    if inner_r >= AXIS_HEIGHT - 1.5:
        reject(
            f"pole_diameter {pole_diameter} is too large to cradle at {AXIS_HEIGHT} mm axis height",
            param="pole_diameter",
        )
    if pole_diameter < 10.0:
        reject(
            f"pole_diameter {pole_diameter} is too small for a 120 degree cradle at {AXIS_HEIGHT} mm axis height",
            param="pole_diameter",
        )

    # Top face sits above the 66 degree point so a 120 degree backed arc remains.
    # Cap below the axis so the pole can drop straight in.
    height = AXIS_HEIGHT - inner_r * cos(radians(66.0)) + 1.4
    height = min(height, AXIS_HEIGHT - 0.8)
    top_gap = AXIS_HEIGHT - height
    groove_half = sqrt(inner_r * inner_r - top_gap * top_gap)
    width = 2.0 * (groove_half + SIDE_WALL)

    body = Box(width, REST_LENGTH, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    groove = Pos(0, 0, AXIS_HEIGHT) * Rot(90, 0, 0) * Cylinder(inner_r, REST_LENGTH + 4.0)
    body = body - groove

    if draft:
        return body
    bed = body.bounding_box().min.Z

    def outer_edge(e):
        # Leave the trough's own edges sharp: polishing the groove lips against
        # the end faces leaves four sliver facets at the corners.
        p = e.center()
        dist = sqrt(p.X * p.X + (p.Z - AXIS_HEIGHT) * (p.Z - AXIS_HEIGHT))
        return e.bounding_box().min.Z > bed + 0.05 and dist > inner_r + 1.5

    keep = body.edges().filter_by(outer_edge)
    return polish(body, keep, 1.0)
