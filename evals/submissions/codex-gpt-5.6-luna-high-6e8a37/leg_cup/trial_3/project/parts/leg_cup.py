from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over cup for the measured rectangular workbench leg.

    leg_width: measured width of the leg entering the pocket
    leg_depth: measured depth of the leg entering the pocket
    lift: provisional floor thickness that raises the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    pocket_depth = 8.0
    pocket_width = leg_width + 0.4
    pocket_depth_xy = leg_depth + 0.4
    outer_width = pocket_width + 2.0 * wall
    outer_depth = pocket_depth_xy + 2.0 * wall
    total_height = lift + pocket_depth

    outer = Pos(0, 0, total_height / 2.0) * Box(outer_width, outer_depth, total_height)
    pocket = Pos(0, 0, lift + pocket_depth / 2.0) * Box(
        pocket_width, pocket_depth_xy, pocket_depth
    )
    return outer - pocket
