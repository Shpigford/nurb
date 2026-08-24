import math

from nurb import *

# The row of rests fixes the interface: the pole runs along Y with its axis
# exactly this far above the bed, whatever the pole's diameter.
AXIS_HEIGHT = 18.0
# Radial gap between seat and pole so the soft finish never touches until it
# is set down; must stay in the 0.1..0.4 band that still counts as cradling.
SEAT_GAP = 0.2
CHAMFER = 1.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), rest_length=24.0,
              shoulder_width=2.5, draft=False):
    """A bench rest that cradles a freshly finished pole while it dries.

    pole_diameter: how wide the pole is that lies in the seat
    rest_length: how long the rest runs along the pole
    shoulder_width: how much flat top sits either side of the seat mouth
    """
    pole_r = pole_diameter / 2.0
    seat_r = pole_r + SEAT_GAP

    if pole_diameter < 6.0:
        reject(
            "pole_diameter %.1f is under 6mm: a seat that small at an 18mm axis "
            "height is a slot, not a cradle; raise it to 6 or more" % pole_diameter,
            param="pole_diameter")
    floor = AXIS_HEIGHT - seat_r
    if floor < 2.0:
        reject(
            "pole_diameter %.1f leaves only %.1fmm of floor under the seat with "
            "the axis fixed at 18mm; keep it at or below %.1f" %
            (pole_diameter, floor, 2.0 * (AXIS_HEIGHT - SEAT_GAP - 2.0)),
            param="pole_diameter")
    if rest_length < 20.0:
        reject(
            "rest_length %.1f is under the 20mm the pole needs to sit on; "
            "raise it to 20 or more" % rest_length, param="rest_length")

    # The top face sits 1.5mm above the seat's 60-degree point, so even after
    # the rim chamfer the intact seat arc stays past 120 degrees, and it stays
    # below the axis so the pole drops straight down into the seat.
    height = AXIS_HEIGHT - 0.5 * seat_r + 1.5
    mouth = math.sqrt(seat_r ** 2 - (AXIS_HEIGHT - height) ** 2)
    half_width = mouth + shoulder_width

    body = Box(2.0 * half_width, rest_length, height,
               align=(Align.CENTER, Align.CENTER, Align.MIN))
    valley = (Pos(0, 0, AXIS_HEIGHT) * Rot(90, 0, 0)
              * Cylinder(seat_r, rest_length + 4.0))
    body = body - valley

    if draft:
        return body
    bed = body.bounding_box().min.Z
    edges = body.edges()
    keep = edges.filter_by(lambda e: e.bounding_box().min.Z > bed) \
        + edges.filter_by(Axis.Z)
    return polish(body, keep, CHAMFER)
