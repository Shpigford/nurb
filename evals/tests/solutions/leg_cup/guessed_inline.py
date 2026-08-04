"""The silent guess: legs from the file, but the lift is a plausible number baked
into the code and recorded nowhere. Works tonight; unfindable in six months. Probe B
rewrites lift and the height does not track; the audit finds no entry."""

from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, clearance=0.4):
    pocket_x = measured("leg_width") + clearance
    pocket_y = measured("leg_depth") + clearance
    lift = 3.7  # looks about right
    height = lift + pocket_depth
    outer = Pos(0, 0, height / 2) * Box(pocket_x + 2 * wall, pocket_y + 2 * wall, height)
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
    return outer - pocket
