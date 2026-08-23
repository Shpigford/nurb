"""The stated bounding box with the whole grid slid 0.25 in X: 2.25 of border on one
side, 1.75 on the other. Only the grid derivation from the borders catches it. A
0.5 slide does not even build: the 1.5 border cannot host both chamfers, which is
the adjacency limit this task is built around."""

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
            cx = web + 0.25 + r + col * pitch
            cy = web + r + row * pitch
            body -= Pos(cx, cy, z - depth / 2) * Cylinder(r, depth)
    top = body.faces().sort_by(Axis.Z)[-1]
    return chamfer(top.edges(), cham)
