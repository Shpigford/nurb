"""Skips the finishing pass entirely: no lead-ins, no perimeter chamfer."""

from nurb import *


@part
def bit_block(shank_diameter=6.5, columns=5):
    web, depth, floor = 2.0, 12.0, 3.0
    pocket_d = shank_diameter + 0.3
    r = pocket_d / 2
    pitch = pocket_d + web
    x = columns * pitch + web
    y = 2 * pitch + web
    z = floor + depth
    body = Pos(x / 2, y / 2, z / 2) * Box(x, y, z)
    for col in range(columns):
        for row in range(2):
            cx = web + r + col * pitch
            cy = web + r + row * pitch
            body -= Pos(cx, cy, z - depth / 2) * Cylinder(r, depth)
    return body
