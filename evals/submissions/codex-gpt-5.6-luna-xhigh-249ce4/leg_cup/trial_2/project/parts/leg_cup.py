from nurb import *


@part
def leg_cup():
    """Slip-over cup for a rectangular workbench leg.

    The pocket is leg_width/depth plus 0.4 mm for a free fit; lift is the
    provisional solid floor thickness that raises the bench.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    wall = 2.0
    floor = lift
    outer_width = pocket_width + 2.0 * wall
    outer_depth = pocket_depth + 2.0 * wall
    total_height = floor + 8.0

    outer = Box(
        outer_width,
        outer_depth,
        total_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(wall, wall, floor) * Box(
        pocket_width,
        pocket_depth,
        8.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return outer - pocket
