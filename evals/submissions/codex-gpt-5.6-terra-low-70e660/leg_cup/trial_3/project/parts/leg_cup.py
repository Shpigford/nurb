from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over leveling cup for the short workbench leg.

    Dimensions are driven only by measurements.toml so a later lift measurement
    updates both the floor and the complete height.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0
    inner_width = leg_width + clearance
    inner_depth = leg_depth + clearance

    outer = Box(
        inner_width + 2.0 * wall_thickness,
        inner_depth + 2.0 * wall_thickness,
        lift + pocket_depth,
    )
    pocket = Box(inner_width, inner_depth, pocket_depth).translate((0, 0, lift))
    return outer.cut(pocket)
