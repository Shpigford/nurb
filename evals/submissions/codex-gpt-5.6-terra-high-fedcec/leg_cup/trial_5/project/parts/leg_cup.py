from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for a rectangular workbench leg.

    The leg dimensions and lift are read from measurements.toml so a later
    measurement changes the mating pocket and floor thickness together.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")
    wall_thickness = 2.0
    clearance = 0.4
    pocket_height = 8.0

    pocket_width = leg_width + clearance
    pocket_depth = leg_depth + clearance
    outer = Box(
        pocket_width + 2 * wall_thickness,
        pocket_depth + 2 * wall_thickness,
        lift + pocket_height,
    )
    pocket = Box(pocket_width, pocket_depth, pocket_height).translate(
        # Boxes are centered on their own origins.  This puts the pocket floor
        # exactly lift above the cup's bottom and leaves it open at the top.
        (0, 0, lift / 2)
    )
    return outer.cut(pocket)
