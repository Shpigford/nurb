"""The reference knob with the doctrine's finishing pass on the top perimeter.
Every stated gate must survive a polish: the grip is measured at half height, below
any chamfer's reach."""

import math

from nurb import *


@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5):
    height, across_flats, clearance = 14.0, 30.0, 0.5
    bore_r = shaft_diameter / 2 + clearance / 2
    flat_x = (shaft_across_flat - shaft_diameter / 2) + clearance / 2
    body = extrude(RegularPolygon(across_flats / math.sqrt(3), 6), height)
    bore = Cylinder(bore_r, height + 2) - Pos(flat_x + 2, 0, 0) * Box(
        4, 2 * bore_r + 2, height + 3
    )
    body -= Pos(0, 0, height / 2) * bore
    top = body.faces().sort_by(Axis.Z)[-1]
    rim = [e for e in top.edges() if e.length > 5.0]  # the outer perimeter, not the bore
    return chamfer(rim, 1.0)
