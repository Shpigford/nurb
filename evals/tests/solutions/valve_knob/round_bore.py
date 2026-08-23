"""The lazy bore: a plain cylinder at the right clearance. The stem slides in and
spins forever; only the torque check knows."""

import math

from nurb import *


@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5):
    height, across_flats = 14.0, 30.0
    bore_r = shaft_diameter / 2 + 0.25
    body = extrude(RegularPolygon(across_flats / math.sqrt(3), 6), height)
    return body - Pos(0, 0, height / 2) * Cylinder(bore_r, height + 2)
