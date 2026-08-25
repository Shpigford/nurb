from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for the workbench's short rectangular leg.

    The leg dimensions and lift are read from measurements.toml so a confirmed
    lift can replace the provisional estimate without editing this model.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall_thickness = 2.0
    clearance = 0.4
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_length = leg_depth + clearance
    outer_width = pocket_width + 2.0 * wall_thickness
    outer_length = pocket_length + 2.0 * wall_thickness
    total_height = lift + pocket_depth

    outer = Box(
        outer_width,
        outer_length,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Box(
        pocket_width,
        pocket_length,
        pocket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, 0, lift))
    return outer - pocket
