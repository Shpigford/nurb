"""A support-free drying rest for a freshly finished pole."""

from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Cradle a pole while its finish dries.

    pole_diameter: diameter of the pole being supported
    """
    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + 0.2

    # The pole axis is at Z=18.0.  Keeping the top below that axis makes the
    # cradle open from above, so the pole can be lowered straight into it.
    axis_height = 18.0
    seat_top = 14.0
    length = 24.0
    wall = 3.0
    width = 2.0 * (seat_radius + wall)

    body = Box(
        width,
        length,
        seat_top,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = Pos(0, 0, axis_height) * Cylinder(
        seat_radius,
        length + 2.0,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return body - seat
