from nurb import *


@part
def leg_cup():
    """Slip-over foot cup.

    leg_width: measured width of the bench leg
    leg_depth: measured depth of the bench leg
    lift: provisional floor thickness that raises the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    height = lift + 8.0
    outer = Pos(0, 0, height / 2.0) * Box(leg_width + 4.4, leg_depth + 4.4, height)
    pocket = Pos(0, 0, lift + 4.0) * Box(leg_width + 0.4, leg_depth + 0.4, 8.0)
    return outer - pocket
