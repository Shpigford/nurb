from nurb import *


@part
def leg_cup():
    """Slip-over rectangular foot cup for leveling a wobbly workbench.

    leg_width: measured width of the bench leg
    leg_depth: measured depth of the bench leg
    lift: provisional floor thickness that raises the bench
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
    )
    pocket = Pos(0, 0, lift / 2) * Box(
        leg_width + 0.4,
        leg_depth + 0.4,
        pocket_depth,
    )
    return outer - pocket
