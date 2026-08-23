"""A perfect cradle in three times the block: every functional gate passes and the
material ladder charges the bulk."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    length, axis_h = 20.0, 18.0
    r = pole_diameter / 2 + 0.2
    width = 3 * (2 * r + 4.8)
    top = axis_h - 0.34 * r
    body = Pos(0, 0, top / 2) * Box(width, length, top)
    return body - Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r, length + 2)
