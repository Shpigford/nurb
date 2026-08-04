"""Cheat A2: the undercut groove alone, no outer relief, so the outer skin still
reaches the bed. Tests whether the dims-stage hole can be reached with clean lint.
"""

from nurb import *

GROOVE = 0.8
SKIN = 0.05


@part
def leg_cup(wall=2.0, pocket_depth=8.0, clearance=0.4):
    pocket_x = measured("leg_width") + clearance
    pocket_y = measured("leg_depth") + clearance
    lift = measured("lift")
    height = lift + pocket_depth
    cup = Pos(0, 0, height / 2) * Box(pocket_x + 2 * wall, pocket_y + 2 * wall, height)
    cup -= Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
    groove_h = lift - SKIN
    cup -= Pos(0, 0, groove_h / 2) * (
        Box(pocket_x + 2 * GROOVE, pocket_y + 2 * GROOVE, groove_h)
        - Box(pocket_x, pocket_y, groove_h + 1.0)
    )
    return cup
