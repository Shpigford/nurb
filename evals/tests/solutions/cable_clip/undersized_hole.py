"""Flawed: 4.2mm rims hide a nearly closed pilot hole through the tab."""

from nurb import *


@part
def cable_clip(bundle_diameter=8.0):
    wall, base, length, tab = 2.4, 3.0, 12.0, 10.0
    channel = bundle_diameter + 0.4
    depth = bundle_diameter
    width = 2 * wall + channel
    body = Pos(width / 2, 0, (base + depth) / 2) * Box(width, length, base + depth)
    cut = Pos(wall + channel / 2, 0, base + depth / 2) * Box(channel, length, depth)
    tab_block = Pos(width + tab / 2, 0, base / 2) * Box(tab, length, base)
    center = width + tab / 2
    pilot = Pos(center, 0, base / 2) * Cylinder(0.2, base)
    bottom_rim = Pos(center, 0, 0.05) * Cylinder(2.1, 0.1)
    top_rim = Pos(center, 0, base - 0.05) * Cylinder(2.1, 0.1)
    return body - cut + tab_block - pilot - bottom_rim - top_rim
