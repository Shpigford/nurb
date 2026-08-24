from nurb import *


@part
def pole_rest(pole_diameter=20.0):
    """A low, open cradle for supporting a freshly finished pole.

    pole_diameter: measured width of the pole that rests in the cradle
    """
    axis_height = 18.0
    clearance = 0.2
    cradle_length = 24.0
    side_backing = 2.8

    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + clearance
    body_width = 2.0 * (seat_radius + side_backing)

    # The block stops at the pole axis, leaving the whole upper half open for
    # straight-down loading. Subtracting the transverse cylinder creates a
    # continuous 180-degree conformal seat along the complete Y length.
    body = Box(body_width, cradle_length, axis_height).translate((0, 0, axis_height / 2.0))
    seat = (
        Cylinder(seat_radius, cradle_length + 2.0)
        .rotate(Axis.X, 90)
        .translate((0, 0, axis_height))
    )
    return body - seat
