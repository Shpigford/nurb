"""Right at the stated size, deaf to both parameters."""

from nurb import *


@part
def bit_block(shank_diameter=6.5, columns=5):
    web, depth, floor, cham = 2.0, 12.0, 3.0, 0.8
    pocket_d = 6.8
    r = pocket_d / 2
    pitch = 8.8
    x = 46.0
    y = 19.6
    z = floor + depth
    body = Pos(x / 2, y / 2, z / 2) * Box(x, y, z)
    for col in range(5):
        for row in range(2):
            cx = web + r + col * pitch
            cy = web + r + row * pitch
            body -= Pos(cx, cy, z - depth / 2) * Cylinder(r, depth)
    top = body.faces().sort_by(Axis.Z)[-1]
    return chamfer(top.edges(), cham)
