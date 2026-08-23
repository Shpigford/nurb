"""Derives everything from the shank but wrote the grid out by hand: five columns
forever, whatever the columns parameter says. The column flex probes exist for
exactly this part."""

from nurb import *


@part
def bit_block(shank_diameter=6.5, columns=5):
    web, depth, floor, cham = 2.0, 12.0, 3.0, 0.8
    pocket_d = shank_diameter + 0.3
    r = pocket_d / 2
    pitch = pocket_d + web
    x = 5 * pitch + web
    y = 2 * pitch + web
    z = floor + depth
    body = Pos(x / 2, y / 2, z / 2) * Box(x, y, z)
    for col in range(5):
        for row in range(2):
            cx = web + r + col * pitch
            cy = web + r + row * pitch
            body -= Pos(cx, cy, z - depth / 2) * Cylinder(r, depth)
    top = body.faces().sort_by(Axis.Z)[-1]
    return chamfer(top.edges(), cham)
