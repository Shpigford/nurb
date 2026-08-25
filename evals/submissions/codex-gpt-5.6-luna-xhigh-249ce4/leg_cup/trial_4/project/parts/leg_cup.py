from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over cup for a 22.0 x 18.5mm rectangular workbench leg.

    leg_width: measured width of the leg entering the pocket
    leg_depth: measured depth of the leg entering the pocket
    lift: provisional floor thickness that raises the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    wall = 2.0
    pocket_height = 8.0
    outer_width = pocket_width + 2.0 * wall
    outer_depth = pocket_depth + 2.0 * wall
    total_height = lift + pocket_height

    body = Box(outer_width, outer_depth, total_height)
    pocket = Pos(0, 0, lift / 2.0) * Box(
        pocket_width, pocket_depth, pocket_height
    )
    return body - pocket
