from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for the short rectangular workbench leg.

    The pocket size follows leg_width and leg_depth from measurements.toml.
    lift: thickness of the solid floor that raises the short leg.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    wall_thickness = 2.0
    side_clearance = 0.4
    pocket_depth = 8.0

    pocket_width = leg_width + side_clearance
    pocket_front_to_back = leg_depth + side_clearance
    total_width = pocket_width + wall_thickness * 2
    total_front_to_back = pocket_front_to_back + wall_thickness * 2
    total_height = lift + pocket_depth

    outer = Box(
        total_width,
        total_front_to_back,
        total_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket_cutter = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_front_to_back,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return outer - pocket_cutter
