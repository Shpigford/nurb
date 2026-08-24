from nurb import *


@part
def leg_cup():
    """A slip-over cup that lifts and steadies the short workbench leg."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_y = leg_depth + clearance
    outer_width = pocket_width + 2.0 * wall
    outer_depth = pocket_depth_y + 2.0 * wall

    body = Box(outer_width, outer_depth, lift + pocket_depth)
    pocket = Pos(0, 0, lift / 2.0) * Box(
        pocket_width,
        pocket_depth_y,
        pocket_depth,
    )
    return body - pocket
