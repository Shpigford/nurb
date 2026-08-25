from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A support-free drying rest for one finished pole.

    pole_diameter: outside diameter of the pole being cradled.
    """
    # The pole axis is deliberately fixed at Z=18. A 0.20 mm radial relief
    # keeps finish clear while the 1.8 mm minimum rim supplies a broad cradle.
    axis_height = 18.0
    clearance = 0.20
    backing = 1.80
    length = 24.0
    inner_radius = pole_diameter / 2.0 + clearance
    outer_half_width = inner_radius + backing

    # Removing the horizontal cylinder leaves its lower half as a 180-degree
    # open-top saddle: it supports broadly but has no material in the drop path.
    blank = Box(2.0 * outer_half_width, length, axis_height).translate(
        (0, 0, axis_height / 2.0)
    )
    seat = Cylinder(inner_radius, length).rotate(Axis.X, 90).translate(
        (0, 0, axis_height)
    )
    return blank - seat
