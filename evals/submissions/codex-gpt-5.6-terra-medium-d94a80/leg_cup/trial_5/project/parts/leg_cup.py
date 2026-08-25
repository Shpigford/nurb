from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over levelling cup for the workbench's short rectangular leg.

    The leg dimensions and lift are intentionally read from measurements.toml so a
    verified shop measurement rebuilds the cup without changing this design.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0

    inner_width = leg_width + clearance
    inner_depth = leg_depth + clearance
    outer_width = inner_width + 2.0 * wall_thickness
    outer_depth = inner_depth + 2.0 * wall_thickness

    outer = Box(
        outer_width,
        outer_depth,
        lift + pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(wall_thickness, wall_thickness, lift) * Box(
        inner_width,
        inner_depth,
        pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return outer - pocket
