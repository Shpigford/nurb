"""A full-height notch in one side leaves the bounding box unchanged but makes
the bottom concave instead of the required full rectangular footprint."""

from nurb import *


@part
def bit_block(shank_diameter=6.5, columns=5):
    web, depth, floor, cham = 2.0, 12.0, 3.0, 0.8
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
    top = body.faces().sort_by(Axis.Z)[-1]
    body = chamfer(top.edges(), cham)
    return body - Pos(0.5, y / 2, z / 2) * Box(1.0, 2.0, z)
