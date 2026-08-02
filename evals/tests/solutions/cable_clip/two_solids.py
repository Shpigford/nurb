"""Flawed: the tab drifted off the body. Two solids is not a part."""

from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    wall, base, length = 2.4, 3.0, 12.0
    channel = bundle_diameter + 0.4
    depth = bundle_diameter
    width = 2 * wall + channel
    body = Pos(width / 2, 0, (base + depth) / 2) * Box(width, length, base + depth)
    tab_block = Pos(width + 20.0, 0, base / 2) * Box(10.0, length, base)
    return body + tab_block
