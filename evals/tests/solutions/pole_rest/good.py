"""The reference solution: a block with the pole's own curve cut out of it. The
cradle radius rides the measured diameter, the rim stops where a 140 degree arc of
contact remains, and nothing else exists."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    """pole_diameter: pole across, from measurements.toml"""
    gap, wall, length, axis_h = 0.2, 2.4, 20.0, 18.0
    r = pole_diameter / 2 + gap
    width = 2 * r + 2 * wall
    top = axis_h - 0.34 * r
    body = Pos(0, 0, top / 2) * Box(width, length, top)
    pocket = Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r, length + 2)
    return body - pocket
