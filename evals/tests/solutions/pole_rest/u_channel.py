"""The other prismatic answer: a square channel, floor and walls at the stated
clearance. Touch at three lines, no arc."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    wall, length, axis_h = 2.4, 20.0, 18.0
    r = pole_diameter / 2 + 0.2
    width = 2 * r + 2 * wall
    top = 13.0
    body = Pos(0, 0, top / 2) * Box(width, length, top)
    body -= Pos(0, 0, (axis_h - r + top + 2) / 2) * Box(2 * r, length + 2, top + 2 - (axis_h - r))
    return body
