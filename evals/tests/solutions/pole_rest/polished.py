"""The reference cradle with the doctrine's finishing pass on its outside edges.
Every stated gate must survive a polish: the arc lives in the pocket, which the
chamfers never touch."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    gap, wall, length, axis_h = 0.2, 2.4, 20.0, 18.0
    r = pole_diameter / 2 + gap
    width = 2 * r + 2 * wall
    top = axis_h - 0.34 * r
    body = Pos(0, 0, top / 2) * Box(width, length, top)
    body -= Pos(0, 0, axis_h) * Rot(90, 0, 0) * Cylinder(r, length + 2)
    outer = body.edges().filter_by(Axis.Z)
    return chamfer(outer, 1.0)
