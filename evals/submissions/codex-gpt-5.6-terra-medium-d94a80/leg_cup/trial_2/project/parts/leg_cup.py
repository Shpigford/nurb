from nurb import *


@part
def leg_cup():
    """Slip-over leveling cup for a rectangular workbench leg."""
    inner_width = measured("leg_width") + 0.4
    inner_depth = measured("leg_depth") + 0.4
    wall_thickness = 2.0
    pocket_depth = 8.0

    outer = Box(inner_width + 2 * wall_thickness,
                inner_depth + 2 * wall_thickness,
                measured("lift") + pocket_depth)
    # Boxes are centered on their own origin.  Centering the pocket in X/Y
    # makes every wall 2 mm; its Z center leaves the measured floor below it.
    pocket = Box(inner_width, inner_depth, pocket_depth).translate(
        (0, 0, measured("lift") / 2))
    return outer.cut(pocket)
