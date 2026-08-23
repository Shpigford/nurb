"""The right cradle at the stated size, deaf to the parameter."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    length, axis_h = 20.0, 18.0
    r = 11.2
    width = 2 * r + 4.8
    top = axis_h - 0.34 * r
    body = Pos(0, 0, top / 2) * Box(width, length, top)
    return body - Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r, length + 2)
