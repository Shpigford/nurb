"""CHEAT: the tunnel is sealed at BOTH ends by 0.09mm membranes tucked inside the
0.1mm inset the retention sampler leaves at each end of the part. The bundle is
'retained' inside a hermetically sealed cavity it can never be inserted into."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    wall = 1.5
    length = 12.0
    s = bundle_diameter + 1.0
    depth = wall + s + wall
    top = wall + s + wall
    plate = 2.4
    plate_h = top + 9.2
    hole_z = top + 4.6
    cap = 0.09  # thinner than the 0.1 station inset

    block = Pos(depth / 2, 0, top / 2) * Box(depth, length, top)
    tunnel = Pos(wall + s / 2, 0, wall + s / 2) * Box(s, length - 2 * cap, s)
    upper = Pos(plate / 2, 0, top + (plate_h - top) / 2) * Box(plate, length, plate_h - top)
    hole = Pos(plate / 2, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, plate)
    return block - tunnel + upper - hole
