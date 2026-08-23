"""The reference solution: a hex knob with a snug D-bore. The hexagon is the grip
(across-flats 30, corners 15.5% past the flats) and the bore gives the stem 0.5 of
diametral clearance, inside the stated 0.3 to 1.0 band."""

import math

from nurb import *


@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5):
    """shaft_diameter, shaft_across_flat: the valve stem's D-section, from
    measurements.toml"""
    height, across_flats, clearance = 14.0, 30.0, 0.5
    bore_r = shaft_diameter / 2 + clearance / 2
    flat_x = (shaft_across_flat - shaft_diameter / 2) + clearance / 2
    body = extrude(RegularPolygon(across_flats / math.sqrt(3), 6), height)
    bore = Cylinder(bore_r, height + 2) - Pos(flat_x + 2, 0, 0) * Box(
        4, 2 * bore_r + 2, height + 3
    )
    return body - Pos(0, 0, height / 2) * bore
