from nurb import *


@part
def leg_cup():
    """Slip-over cup that lifts and steadies the short workbench leg."""
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

    body = Box(
        outer_width,
        outer_depth,
        lift + pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth_y,
        pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - pocket
