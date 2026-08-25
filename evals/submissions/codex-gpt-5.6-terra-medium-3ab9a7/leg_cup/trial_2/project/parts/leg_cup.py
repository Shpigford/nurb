from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for a rectangular workbench leg.

    The fit and lift are read from measurements.toml so a later measurement
    rebuilds the same design at the corrected height.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall_thickness = 2.0
    clearance = 0.4
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_y = leg_depth + clearance
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
