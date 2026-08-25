from nurb import *


@part
def leg_cup():
    """Slip-over foot cup for a rectangular workbench leg.

    leg_width and leg_depth: measured outside dimensions of the leg.
    lift: provisional solid floor thickness that raises the bench.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0

    outer_width = leg_width + clearance + 2.0 * wall
    outer_depth = leg_depth + clearance + 2.0 * wall
    outer_height = lift + pocket_depth

    body = Box(
        outer_width,
        outer_depth,
        outer_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(wall, wall, lift) * Box(
        leg_width + clearance,
        leg_depth + clearance,
        pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return body - pocket
