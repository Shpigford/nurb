from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for the workbench's short rectangular leg."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall_thickness = 2.0
    clearance = 0.4
    pocket_depth = 8.0

    outer = Box(
        leg_width + clearance + 2 * wall_thickness,
        leg_depth + clearance + 2 * wall_thickness,
        lift + pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Box(
        leg_width + clearance,
        leg_depth + clearance,
        pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, 0, lift))

    return outer - pocket
