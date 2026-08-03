from nurb import *

@part
def leg_cup(
    leg_width: float = 22.0,
    leg_depth: float = 18.5,
    lift: float = 3.0
):
    """A slip-over foot cup to level a wobbly workbench.

    The workbench leg drops into the pocket from above. The solid base
    floor lifts the bench level when the cup sits on the floor.
    """

    # Pocket dimensions with 0.4 mm clearance
    pocket_width = leg_width + 0.4
    pocket_depth = leg_depth + 0.4
    pocket_height = 8.0
    wall_thickness = 2.0

    # Outer bounding box dimensions
    outer_width = pocket_width + 2 * wall_thickness
    outer_depth = pocket_depth + 2 * wall_thickness
    total_height = lift + pocket_height

    # Create the solid base block
    cup = Box(outer_width, outer_depth, total_height)

    # Create the pocket void to cut from the top
    # Centered box range: -h/2 to +h/2; pocket floor should be at -total_h/2 + lift
    # Shift the pocket so its floor aligns correctly
    pocket_void = Box(pocket_width, pocket_depth, pocket_height)
    pocket_shift_z = lift + pocket_height / 2 - total_height / 2
    pocket_void = pocket_void.translate((0, 0, pocket_shift_z))

    # Cut the pocket out, leaving walls and base floor
    cup = cup - pocket_void

    return cup
