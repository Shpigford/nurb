from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over cup for a rectangular bench leg.

    leg_width: measured width of the leg section
    leg_depth: measured depth of the leg section
    lift: provisional floor thickness that raises the bench
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0
    pocket_width = leg_width + clearance
    pocket_depth_xy = leg_depth + clearance
    outer_width = pocket_width + 2.0 * wall
    outer_depth = pocket_depth_xy + 2.0 * wall
    total_height = lift + pocket_depth

    body = Box(
        outer_width,
        outer_depth,
        total_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(wall, wall, lift) * Box(
        pocket_width,
        pocket_depth_xy,
        pocket_depth + 0.2,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return body - pocket
