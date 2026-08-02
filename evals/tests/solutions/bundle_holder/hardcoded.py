"""A snug tunnel sized for the 8.0 bundle and deaf to its parameter. A hardcoded
U-channel with a tall plate can wedge a grown bundle and honestly keep functioning;
a snug tunnel cannot, which is what makes this one the flex probes' quarry."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    length = 12.0
    outer = 12.6  # a 8.6 tunnel plus 2.0 walls, regardless of the measurement
    body = Pos(outer / 2, 0, outer / 2) * Box(outer, length, outer)
    tunnel = Pos(outer / 2, 0, outer / 2) * Rot(90, 0, 0) * Cylinder(4.3, length)
    plate = Pos(1.2, 0, outer + 4.5) * Box(2.4, length, 9.0)
    hole = Pos(1.2, 0, outer + 4.6) * Rot(0, 90, 0) * Cylinder(2.2, 2.4)
    return body + plate - tunnel - hole
