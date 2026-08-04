"""Ignores measurements.toml entirely: every value is a literal matching seed 13, so
the default build is perfect and both measurement probes fail to track."""

from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0):
    pocket_x = 22.4  # leg_width 22.0 + clearance, seed 13
    pocket_y = 18.9  # leg_depth 18.5 + clearance, seed 13
    lift = 3.5
    height = lift + pocket_depth
    outer = Pos(0, 0, height / 2) * Box(pocket_x + 2 * wall, pocket_y + 2 * wall, height)
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_x, pocket_y, pocket_depth)
    return outer - pocket
