from nurb import *


@part
def leg_cup():
    """Slip-over foot cup for a 22 x 18.5 mm workbench leg.

    leg_width: measured width of the leg
    leg_depth: measured depth of the leg
    lift: provisional floor thickness that raises the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    outer = Box(
        leg_width + 4.4,
        leg_depth + 4.4,
        lift + 8.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(2.0, 2.0, lift) * Box(
        leg_width + 0.4,
        leg_depth + 0.4,
        8.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return outer - pocket
