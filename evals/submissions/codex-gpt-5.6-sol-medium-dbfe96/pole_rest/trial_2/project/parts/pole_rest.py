from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter")):
    """A low, full-length cradle for a freshly finished pole.

    pole_diameter: measured width of the pole held by the cradle
    """
    axis_height = 18.0
    clearance = 0.2
    seat_radius = pole_diameter / 2.0 + clearance

    length = 24.0
    body_width = pole_diameter + 4.0
    body_height = axis_height - seat_radius * 0.48

    body = Box(body_width, length, body_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    seat = Cylinder(
        seat_radius,
        length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).rotate(Axis.X, 90).translate((0, 0, axis_height))

    return body - seat
