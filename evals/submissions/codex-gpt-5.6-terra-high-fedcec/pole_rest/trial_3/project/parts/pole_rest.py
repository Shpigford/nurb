from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A low, continuously curved drying cradle for a finished pole.

    pole_diameter: diameter of the pole resting in the cradle
    """
    clearance = 0.15
    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + clearance
    side_backing = 1.5

    # The top of the printed base is the fixed 18 mm pole axis.  Removing the
    # lower half of this longitudinal cylinder leaves a 180-degree U-cradle.
    base_width = 2.0 * (seat_radius + side_backing)
    base = Box(base_width, 30.0, 18.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    seat = Pos(0, 0, 18.0) * Rot(-90.0, 0, 0) * Cylinder(seat_radius, 30.0)
    return base - seat
