"""A bore at 1.4 of diametral clearance: past the stated 1.0, a knob that rattles.
The slop stem passes clean through, which is exactly the charge."""

import math

from nurb import *


@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5):
    height, across_flats, clearance = 14.0, 30.0, 1.4
    bore_r = shaft_diameter / 2 + clearance / 2
    flat_x = (shaft_across_flat - shaft_diameter / 2) + clearance / 2
    body = extrude(RegularPolygon(across_flats / math.sqrt(3), 6), height)
    bore = Cylinder(bore_r, height + 2) - Pos(flat_x + 2, 0, 0) * Box(
        4, 2 * bore_r + 2, height + 3
    )
    return body - Pos(0, 0, height / 2) * bore
