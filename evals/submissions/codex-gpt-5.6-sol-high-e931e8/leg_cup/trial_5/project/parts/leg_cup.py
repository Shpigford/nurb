from nurb import *


@part
def leg_cup():
    """A floor-standing cup that lifts and steadies the short bench leg."""
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0

    pocket_width = leg_width + clearance
    pocket_depth_width = leg_depth + clearance
    outside_width = pocket_width + 2.0 * wall_thickness
    outside_depth = pocket_depth_width + 2.0 * wall_thickness
    overall_height = lift + pocket_depth
    cutter_height = pocket_depth + 0.1

    body = Pos(0, 0, overall_height / 2.0) * Box(
        outside_width,
        outside_depth,
        overall_height,
    )
    pocket = Pos(0, 0, lift + cutter_height / 2.0) * Box(
        pocket_width,
        pocket_depth_width,
        cutter_height,
    )

    return body - pocket
