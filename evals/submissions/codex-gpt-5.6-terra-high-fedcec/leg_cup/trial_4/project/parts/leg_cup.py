from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for the workbench's short leg.

    draft: skips no features; retained for the standard part interface.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall_thickness = 2.0
    pocket_clearance = 0.4
    pocket_depth = 8.0

    pocket_width = leg_width + pocket_clearance
    pocket_depth_y = leg_depth + pocket_clearance
    total_height = lift + pocket_depth

    outer = Box(
        pocket_width + 2 * wall_thickness,
        pocket_depth_y + 2 * wall_thickness,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Box(
        pocket_width,
        pocket_depth_y,
        pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, 0, lift))
    return outer - pocket
