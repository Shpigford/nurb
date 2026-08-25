from nurb import *


@part
def leg_cup():
    """Slip-over cup that lifts and steadies the short workbench leg."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    wall = 2.0
    pocket_height = 8.0

    outer = Box(
        pocket_width + 2.0 * wall,
        pocket_depth + 2.0 * wall,
        lift + pocket_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth,
        pocket_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return outer - pocket
