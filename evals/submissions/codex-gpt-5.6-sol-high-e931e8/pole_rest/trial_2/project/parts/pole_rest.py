from math import cos, radians

from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter")):
    """A bench rest that cradles a freshly finished pole while it dries.

    pole_diameter: the measured diameter of the pole being supported
    """
    axis_height = 18.0
    clearance = 0.2
    seat_radius = pole_diameter / 2.0 + clearance

    length = 24.0
    width = pole_diameter + 8.0

    # Ending the block slightly above the 120-degree chord leaves a generous
    # continuous cradle arc while keeping the entire top open for drop-in use.
    cradle_half_angle = 62.0
    top_height = axis_height - seat_radius * cos(radians(cradle_half_angle))

    body = Box(
        width,
        length,
        top_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = Pos(0, 0, axis_height) * Rot(90, 0, 0) * Cylinder(
        seat_radius,
        length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    return body - seat
