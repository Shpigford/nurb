from nurb import *


@part
def pole_rest(pole_diameter: float = 20.0):
    """A soft-finish drying rest with a long, close-fitting cradle.

    pole_diameter: measured diameter of the pole being supported
    """
    axis_height = 18.0
    clearance = 0.2
    cradle_radius = pole_diameter / 2 + clearance
    length = 24.0
    width = pole_diameter + 5.0
    top_height = axis_height - 0.1

    body = Box(
        width,
        length,
        top_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pole_space = Cylinder(
        cradle_radius,
        length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).rotate(Axis.X, 90).translate((0, 0, axis_height))

    return body - pole_space
