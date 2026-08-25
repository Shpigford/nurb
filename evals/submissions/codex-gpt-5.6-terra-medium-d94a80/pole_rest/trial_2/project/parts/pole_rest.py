from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A support-free drying cradle for a pole.

    pole_diameter: measured diameter of the pole being supported.
    """
    # The pole axis is deliberately fixed at z=18.  A 0.2 mm radial gap keeps
    # fresh finish off the rest while remaining close enough to support it.
    axis_height = 18.0
    rest_length = 30.0
    base_width = 25.5
    top_height = 13.4
    clearance_radius = pole_diameter / 2.0 + 0.2

    base = Box(
        base_width,
        rest_length,
        top_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bore = Cylinder(clearance_radius, rest_length).rotate(Axis.X, -90)
    bore = Pos(0, 0, axis_height) * bore
    return base - bore
