from nurb import *


@part
def leg_cup(draft=False):
    """A slip-over cup that lifts one rectangular workbench leg.

    The fit and lift come from measurements.toml so corrected shop measurements
    rebuild the printable geometry without changing this file.
    """
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

    min_corner = (Align.MIN, Align.MIN, Align.MIN)
    body = Box(
        outer_width,
        outer_depth,
        lift + pocket_depth,
        align=min_corner,
    )
    pocket = Pos(wall, wall, lift) * Box(
        pocket_width,
        pocket_depth_y,
        pocket_depth,
        align=min_corner,
    )
    return body - pocket
