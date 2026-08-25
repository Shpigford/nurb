from nurb import *


@part
def pole_rest(pole_diameter=20.0, draft=False):
    """A support-free drying rest for a finished pole.

    pole_diameter: diameter of the pole being cradled
    """
    pole_radius = pole_diameter / 2.0
    clearance = 0.1
    seat_radius = pole_radius + clearance
    length = 20.0
    width = pole_diameter + 4.0
    axis_height = 18.0

    body = Pos(0, 0, axis_height / 2.0) * Box(
        width, length, axis_height
    )

    # The cylinder is coaxial with Y.  Its lower semicircle is an uninterrupted
    # cradle; the rectangular body stops at the pole centreline for drop-in access.
    seat_cut = (
        Pos(0, -length / 2.0, axis_height)
        * Rot(-90, 0, 0)
        * Cylinder(seat_radius, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    result = body - seat_cut

    return result
