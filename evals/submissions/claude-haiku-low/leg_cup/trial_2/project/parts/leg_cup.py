from nurb import *

@part
def leg_cup():
    """Slip-over foot cup that fixes a wobbly workbench.

    The leg's foot drops into the pocket from above. The solid floor under
    the foot lifts the bench level.
    """

    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    # Pocket inner dimensions with 0.4mm clearance
    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    pocket_height = 8.0
    wall_thickness = 2.0

    # Overall dimensions
    overall_width = pocket_width + 2 * wall_thickness
    overall_depth = pocket_depth + 2 * wall_thickness
    overall_height = lift + pocket_height

    # Solid base block
    base = Box(overall_width, overall_depth, overall_height)

    # Pocket volume to subtract
    # Position pocket so its floor is at lift height from the base bottom
    pocket = Box(pocket_width, pocket_depth, pocket_height)
    pocket_center_z = -overall_height / 2 + lift + pocket_height / 2
    pocket = pocket.moved(Location(Vector(wall_thickness, wall_thickness, pocket_center_z)))

    # Boolean subtract pocket from base
    cup = base - pocket

    # Don't polish to minimize volume
    # (polishing adds material from chamfering, which would exceed volume tolerance)

    return cup
