from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup that lifts a short workbench leg level.

    The pocket is the measured leg plus 0.4 mm of clearance. Walls are 2 mm
    on all four sides. Floor thickness is lift from measurements.toml, which
    is still a guess until the bench can be measured.
    """
    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0
    lift = measured("lift")
    pocket_w = measured("leg_width") + clearance
    pocket_d = measured("leg_depth") + clearance
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    height = lift + pocket_depth

    body = Box(outer_w, outer_d, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Cut past the rim so coplanar top faces cannot leave a film over the pocket.
    cavity = Box(
        pocket_w,
        pocket_d,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((0, 0, lift)))
    cup = body - cavity
    if draft:
        return cup
    # No polish: a 1 mm chamfer on 2 mm walls would knife-edge the rim, and the
    # pocket, walls, and bounding box have to stay at the stated sizes.
    return cup
