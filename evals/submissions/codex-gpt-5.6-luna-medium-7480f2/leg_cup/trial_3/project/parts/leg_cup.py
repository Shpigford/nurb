from nurb import *


@part
def leg_cup():
    """Slip-over foot cup for leveling a rectangular workbench leg.

    leg_width: measured width of the leg
    leg_depth: measured front-to-back depth of the leg
    lift: provisional solid floor thickness that raises the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    pocket_depth = 8.0
    outer = Box(
        leg_width + 0.4 + 2 * wall,
        leg_depth + 0.4 + 2 * wall,
        lift + pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        leg_width + 0.4,
        leg_depth + 0.4,
        pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return outer - pocket
