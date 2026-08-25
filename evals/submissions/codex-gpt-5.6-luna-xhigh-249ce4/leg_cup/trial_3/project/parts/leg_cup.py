from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup for leveling a rectangular workbench leg.

    leg_width: measured width of the short leg
    leg_depth: measured depth of the short leg
    lift: provisional floor thickness that raises the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall = 2.0
    pocket_depth = 8.0
    pocket_clearance = 0.4

    outer_width = leg_width + pocket_clearance + 2.0 * wall
    outer_depth = leg_depth + pocket_clearance + 2.0 * wall
    total_height = lift + pocket_depth

    outer = Box(
        outer_width,
        outer_depth,
        total_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(wall, wall, lift) * Box(
        leg_width + pocket_clearance,
        leg_depth + pocket_clearance,
        pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return outer - pocket
