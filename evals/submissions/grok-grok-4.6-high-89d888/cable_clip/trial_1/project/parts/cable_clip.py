from nurb import *

# Fit-critical numbers the clip is specified at, in mm.
_WALL = 2.4
_BASE = 3.0
_LENGTH = 12.0
_TAB = 10.0
_HOLE = 4.2
_CLEARANCE = 0.4


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle against a surface.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    channel_width = bundle_diameter + _CLEARANCE
    channel_depth = bundle_diameter
    body_width = _WALL + channel_width + _WALL
    hole_x = body_width + _TAB / 2
    hole_y = _LENGTH / 2

    base = Box(body_width + _TAB, _LENGTH, _BASE, align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Box(_WALL, _LENGTH, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN))
    left_wall = Pos(0, 0, _BASE) * left_wall
    right_wall = Box(_WALL, _LENGTH, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN))
    right_wall = Pos(_WALL + channel_width, 0, _BASE) * right_wall
    body = base + left_wall + right_wall

    hole = Cylinder(_HOLE / 2, _BASE + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hole = Pos(hole_x, hole_y, -1) * hole
    body = body - hole
    return body
