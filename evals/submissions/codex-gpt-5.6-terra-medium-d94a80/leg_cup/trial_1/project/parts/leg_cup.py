from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for the workbench's short rectangular leg.

    The leg dimensions and lift are read from measurements.toml so the cup follows
    the recorded fit and the eventual measured leveling height.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall_thickness = 2.0
    clearance = 0.4
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_y = leg_depth + clearance
    overall_height = lift + pocket_depth

    outside = Box(
        pocket_width + 2.0 * wall_thickness,
        pocket_depth_y + 2.0 * wall_thickness,
        overall_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_depth_y,
        pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return outside - pocket
