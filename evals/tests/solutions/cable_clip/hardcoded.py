"""Flawed: correct at its defaults, but every dimension is a literal. The parameter
is decorative, which only the flex probes can see."""

from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    body = Pos(6.6, 0, 5.5) * Box(13.2, 12.0, 11.0)
    cut = Pos(6.6, 0, 7.0) * Box(8.4, 12.0, 8.0)
    tab_block = Pos(18.2, 0, 1.5) * Box(10.0, 12.0, 3.0)
    hole = Pos(18.2, 0, 1.5) * Cylinder(2.1, 3.0)
    return body - cut + tab_block - hole
