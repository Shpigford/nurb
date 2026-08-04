from nurb import *

@part
def leg_cup():
    """Slip-over foot cup to fix a wobbly workbench."""

    # Get measurements from measurements.toml
    leg_w = measured("leg_width")
    leg_d = measured("leg_depth")
    lift_h = measured("lift")

    # Pocket dimensions (0.4 mm clearance)
    pocket_w = leg_w + 0.4
    pocket_d = leg_d + 0.4
    pocket_depth = 8.0

    # Wall thickness
    wall_t = 2.0

    # Overall dimensions
    overall_w = pocket_w + 2 * wall_t
    overall_d = pocket_d + 2 * wall_t
    overall_h = lift_h + pocket_depth

    # Create solid block for the cup
    result = Box(overall_w, overall_d, overall_h)

    # Subtract the pocket from the top
    # Pocket positioned at (wall_t, wall_t, lift_h)
    pocket = Box(pocket_w, pocket_d, pocket_depth)
    pocket = pocket.locate(Location((wall_t, wall_t, lift_h)))
    result = result - pocket

    return result
