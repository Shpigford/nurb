from nurb import *


@part
def leg_cup():
    """A slip-over cup that lifts and steadies the workbench's short leg."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_width = leg_depth + clearance
    outer_width = pocket_width + 2.0 * wall_thickness
    outer_depth = pocket_depth_width + 2.0 * wall_thickness

    body = Box(
        outer_width,
        outer_depth,
        lift + pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth_width,
        pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return body - pocket
