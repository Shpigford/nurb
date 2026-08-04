"""The reference: every dimension from the file, nothing baked in. The honest lift
entry it relies on is written by the test harness (see test_leg_cup.LIFT_ENTRIES),
because that edit is part of the graded behaviour, not of the part."""

from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, clearance=0.4):
    """wall: cup wall thickness. pocket_depth: how far the leg drops in."""
    pocket_x = measured("leg_width") + clearance
    pocket_y = measured("leg_depth") + clearance
    lift = measured("lift")
    height = lift + pocket_depth
    outer = Pos(0, 0, height / 2) * Box(pocket_x + 2 * wall, pocket_y + 2 * wall, height)
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
    return outer - pocket
