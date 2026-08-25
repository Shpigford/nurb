from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A support-free drying cradle for a finished pole.

    pole_diameter: diameter of the pole being held
    """
    pole_radius = pole_diameter / 2.0
    clearance = 0.15
    inner_radius = pole_radius + clearance

    # The pole axis is deliberately a fixed datum: the cradle scales around it.
    axis_height = 18.0
    length = 24.0
    # A broad, grounded shell supplies radial backing while its straight outside
    # walls stay printable. The 24 mm footprint leaves more than 1.2 mm behind
    # every point of the supported lower arc.
    base_width = 2.0 * inner_radius + 4.0
    outer = Box(
        base_width,
        length,
        axis_height - 5.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Cut a circular pocket whose bottom is at 7.9 mm. At the 13 mm mouth the
    # circular wall has reached 120 degrees of pole circumference, while the
    # open top keeps the drop-in path clear.
    inner = Pos(0, -length / 2.0, axis_height) * Rot(-90, 0, 0) * Cylinder(
        inner_radius,
        length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = outer - inner

    if draft:
        return body

    return body
