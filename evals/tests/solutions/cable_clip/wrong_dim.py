"""Flawed: the channel is cut 1mm narrower than stated. Outer envelope still right,
so only the floor-span assertion can catch it."""

from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    wall, base, length, tab, hole_r = 2.4, 3.0, 12.0, 10.0, 2.1
    channel = bundle_diameter + 0.4
    depth = bundle_diameter
    width = 2 * wall + channel
    body = Pos(width / 2, 0, (base + depth) / 2) * Box(width, length, base + depth)
    cut = Pos(wall + channel / 2, 0, base + depth / 2) * Box(channel - 1.0, length, depth)
    tab_block = Pos(width + tab / 2, 0, base / 2) * Box(tab, length, base)
    hole = Pos(width + tab / 2, 0, base / 2) * Cylinder(hole_r, base)
    return body - cut + tab_block - hole
