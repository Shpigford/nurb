from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for the workbench's short rectangular leg.

    The pocket receives the measured leg with 0.4 mm total clearance. The
    provisional lift comes from measurements.toml so it can be corrected after
    the bench is checked without changing this part.
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
        pocket_width + 2 * wall_thickness,
        pocket_depth_y + 2 * wall_thickness,
        overall_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    pocket = Pos(wall_thickness, wall_thickness, lift) * Box(
        pocket_width,
        pocket_depth_y,
        pocket_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    return outside - pocket
