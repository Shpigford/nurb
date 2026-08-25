from math import cos, radians

from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A support-free bench rest for a freshly finished pole.

    pole_diameter: measured diameter of the pole held by the cradle
    """
    axis_height = 18.0
    radial_clearance = 0.20
    supported_arc = 130.0
    rest_width = pole_diameter + 8.0
    rest_length = 24.0

    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + radial_clearance
    top_height = axis_height - seat_radius * cos(radians(supported_arc / 2.0))

    body = Box(
        rest_width,
        rest_length,
        top_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = (
        Pos(0, 0, axis_height)
        * Rot(90, 0, 0)
        * Cylinder(
            seat_radius,
            rest_length + 2.0,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
    )

    return body - seat
