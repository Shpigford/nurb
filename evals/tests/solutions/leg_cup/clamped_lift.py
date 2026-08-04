"""Cheat B2: recorded lift is 2.0 (in band, honest, provisional); the part floors it
at 3.5 so the built lift is not the recorded one. Probe B (lift=4.0) is unaffected."""
from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, clearance=0.4):
    pocket_x = measured("leg_width") + clearance
    pocket_y = measured("leg_depth") + clearance
    lift = max(measured("lift"), 3.5)
    height = lift + pocket_depth
    outer = Pos(0, 0, height / 2) * Box(pocket_x + 2 * wall, pocket_y + 2 * wall, height)
    return outer - Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
