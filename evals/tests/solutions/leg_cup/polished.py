"""The doctrine-following positive control: the reference cup with the rim edges
broken by the polish pass, which the shipped skill teaches. Scores 1.0, or the task
is fighting nurb's own doctrine (the phase 3 scorer bug)."""

from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, clearance=0.4):
    pocket_x = measured("leg_width") + clearance
    pocket_y = measured("leg_depth") + clearance
    lift = measured("lift")
    height = lift + pocket_depth
    outer = Pos(0, 0, height / 2) * Box(pocket_x + 2 * wall, pocket_y + 2 * wall, height)
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
    cup = outer - pocket
    rim = cup.edges().filter_by(lambda e: e.bounding_box().min.Z > height - 1e-3)
    return polish(cup, rim, 1.0)
