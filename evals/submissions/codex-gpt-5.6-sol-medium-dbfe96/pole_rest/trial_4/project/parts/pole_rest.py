from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A bench rest that cradles a freshly finished pole while it dries.

    pole_diameter: measured width of the pole held by the rest
    """
    axis_height = 18.0
    clearance = 0.2
    cradle_length = 24.0
    side_backing = 2.8

    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + clearance
    body_width = 2.0 * (seat_radius + side_backing)

    body = Box(
        body_width,
        cradle_length,
        axis_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = Cylinder(
        seat_radius,
        cradle_length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
        rotation=(90, 0, 0),
    ).moved(Pos(0, 0, axis_height))

    # The cylinder's lower half removes a smooth, open-topped 180-degree trough.
    # Its upper half is already outside the body, leaving a straight drop-in path.
    return body - seat
