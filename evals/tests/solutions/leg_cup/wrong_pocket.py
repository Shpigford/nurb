"""Broken geometry, honest paperwork: reads all three measurements but slips 1.2mm of
clearance in, so the pocket, bounding box, and wall probes all miss at every size."""

from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, clearance=1.2):
    pocket_x = measured("leg_width") + clearance
    pocket_y = measured("leg_depth") + clearance
    lift = measured("lift")
    height = lift + pocket_depth
    outer = Pos(0, 0, height / 2) * Box(pocket_x + 2 * wall, pocket_y + 2 * wall, height)
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
    return outer - pocket
