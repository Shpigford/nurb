"""A 0.6mm shell tracing the perfect arc on a pedestal: contact everywhere, nothing
behind it. The backing probe is what has to see through this."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    length, axis_h = 20.0, 18.0
    r = pole_diameter / 2 + 0.3
    shell = Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r + 0.6, length)
    shell -= Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r, length + 2)
    shell -= Pos(0, 0, axis_h - 0.34 * r + 50) * Box(2 * r + 4, length + 2, 100)
    base_top = axis_h - pole_diameter / 2 - 0.4
    base = Pos(0, 0, base_top / 2) * Box(12, length, base_top)
    return shell + base
