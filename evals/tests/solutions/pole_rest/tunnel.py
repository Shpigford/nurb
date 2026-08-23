"""A closed ring around the pole: fit and arc are immaculate and the pole can never
be laid in. The drop-in sweep is what has to catch it."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    length, axis_h = 20.0, 18.0
    r = pole_diameter / 2 + 0.2
    body = Pos(0, 0, (axis_h + r + 2.4) / 2) * Box(2 * r + 4.8, length, axis_h + r + 2.4)
    body -= Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r, length + 2)
    return body
