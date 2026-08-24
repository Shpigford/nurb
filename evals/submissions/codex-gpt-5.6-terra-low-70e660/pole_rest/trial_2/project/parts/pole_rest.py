from nurb import *


@part
def pole_rest(pole_diameter=20.0, length=20.0, draft=False):
    """A support-free, full-length drying cradle for a finished pole.

    pole_diameter: measured diameter of the pole being supported
    length: distance along the pole covered by this rest
    """
    # The pole axis is a fixed datum: do not move it when the pole diameter changes.
    axis_height = 18.0
    pole_radius = pole_diameter / 2.0
    clearance = 0.20
    seat_radius = pole_radius + clearance

    # A 16 mm high block with the horizontal cylinder removed leaves a 157 degree
    # circular lower cradle. Its open top lets the pole descend vertically into it.
    body_width = 2.0 * (seat_radius + 6.2)
    body_height = axis_height - 2.0
    body = Box(
        body_width,
        length,
        body_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = Cylinder(
        seat_radius,
        length + 2.0,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).translate((0, 0, axis_height))
    return body - seat
