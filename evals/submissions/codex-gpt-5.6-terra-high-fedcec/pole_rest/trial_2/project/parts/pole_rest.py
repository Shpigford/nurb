from math import cos, radians

from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """A support-free drying cradle for a finished pole.

    pole_diameter: diameter of the pole held by the cradle
    """
    axis_height = 18.0
    clearance = 0.2
    cradle_radius = pole_diameter / 2.0 + clearance
    length = 26.0
    width = pole_diameter + 7.0

    # The open top is at 70 degrees from the bottom of the pole.  This leaves
    # a 140-degree cushioned arc while every exposed inner wall rises at 45
    # degrees or steeper for support-free printing.
    lip_angle = 70.0
    height = axis_height - cradle_radius * cos(radians(lip_angle))

    body = Box(width, length, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cutter = Pos(0, 0, axis_height) * Cylinder(
        cradle_radius, length + 2.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    ).rotate(Axis.X, 90)
    return body - cutter
