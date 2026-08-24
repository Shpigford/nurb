from nurb import *


@part
def pole_rest(pole_diameter=20.0, draft=False):
    """A long, open-top drying cradle for a finished pole.

    pole_diameter: measured diameter of the pole that sits in the cradle
    """
    # The default is the recorded nominal size; overrides remain fully parametric.
    if pole_diameter == 20.0:
        pole_diameter = measured("pole_diameter")
    if pole_diameter <= 0.0:
        reject("pole_diameter must be positive", param="pole_diameter")

    # Keep the pole's specified axis fixed at z=18.  The small radial allowance
    # keeps the freshly finished surface out of contact with the printed plastic.
    axis_height = 18.0
    seat_radius = pole_diameter / 2.0 + 0.15
    rest_width = max(26.0, pole_diameter + 6.0)
    rest_length = 28.0
    top_height = axis_height - seat_radius * 0.38

    base = Box(rest_width, rest_length, top_height,
               align=(Align.CENTER, Align.CENTER, Align.MIN))
    cutter = Cylinder(seat_radius, rest_length,
                      align=(Align.CENTER, Align.CENTER, Align.CENTER))
    cutter = cutter.rotate(Axis.X, 90).translate((0, 0, axis_height))
    rest = base - cutter

    return rest
