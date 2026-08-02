"""CHEAT: closed square tunnel with a hidden full-cross-section septum wall placed
between the retention sampler's Y-stations (span 12 -> stations at 0.1+k*1.9667 from
min Y). The bundle can never be threaded through: a 1.25mm solid wall blocks the
tunnel at mid-length, invisible to every cross-section station."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    wall = 1.5
    length = 12.0
    s = bundle_diameter + 1.0  # square tunnel side
    depth = wall + s + wall
    top = wall + s + wall
    plate = 2.4
    plate_h = top + 9.2
    hole_z = top + 4.6

    block = Pos(depth / 2, 0, top / 2) * Box(depth, length, top)
    tunnel = Pos(wall + s / 2, 0, wall + s / 2) * Box(s, length + 1, s)
    # stations sit at bb.min.Y + 0.1 + k * (span - 0.2) / 6; for span 12 and
    # centered Y that is ..., 0.0, 1.9667, ...; the septum hides between them.
    septum = Pos(wall + s / 2, 0.975, wall + s / 2) * Box(s, 1.25, s)
    upper = Pos(plate / 2, 0, top + (plate_h - top) / 2) * Box(plate, length, plate_h - top)
    hole = Pos(plate / 2, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, plate)
    return block - tunnel + septum + upper - hole
