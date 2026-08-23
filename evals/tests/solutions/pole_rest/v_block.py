"""The classic prismatic answer: a 90 degree V-block, walls tangent to the pole
with the stated clearance. The pole sits at exactly the right height and touches
along two lines; the arc gate is what has to reject it."""

from nurb import *


@part
def pole_rest(pole_diameter=22.0):
    length, axis_h = 20.0, 18.0
    r = pole_diameter / 2 + 0.2
    vertex = axis_h - r * 2**0.5
    body = Pos(0, 0, 6.5) * Box(34, length, 13)
    # The vee is a diamond: a square prism stood on its corner, walls at 45 degrees
    # through the vertex, tangent to the pole's clearance circle.
    body -= Pos(0, 0, vertex + 50 / 2**0.5) * Rot(0, 45, 0) * Box(50, length + 2, 50)
    return body
