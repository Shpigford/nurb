from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for the workbench's short rectangular leg.

    The leg fit and the unmeasured leveling lift are read from measurements.toml.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_y = leg_depth + clearance
    outer_width = pocket_width + 2.0 * wall_thickness
    outer_depth = pocket_depth_y + 2.0 * wall_thickness

    outer = Box(outer_width, outer_depth, lift + pocket_depth,
                align=(Align.MIN, Align.MIN, Align.MIN))
    pocket = Box(pocket_width, pocket_depth_y, pocket_depth,
                 align=(Align.MIN, Align.MIN, Align.MIN)).translate(
                     (wall_thickness, wall_thickness, lift)
                 )
    return outer - pocket
