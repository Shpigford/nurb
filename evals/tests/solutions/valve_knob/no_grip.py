"""A perfect bore in a plain round puck: nothing for wet hands to push against."""

from nurb import *


@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5):
    height, clearance = 14.0, 0.5
    bore_r = shaft_diameter / 2 + clearance / 2
    flat_x = (shaft_across_flat - shaft_diameter / 2) + clearance / 2
    body = Pos(0, 0, height / 2) * Cylinder(16.0, height)
    bore = Cylinder(bore_r, height + 2) - Pos(flat_x + 2, 0, 0) * Box(
        4, 2 * bore_r + 2, height + 3
    )
    return body - Pos(0, 0, height / 2) * bore
