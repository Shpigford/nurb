from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup that seats a short workbench leg and lifts it level.

    The pocket, walls, and floor all come from the three names in
    measurements.toml: leg_width, leg_depth, and lift.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0

    pocket_x = leg_width + clearance
    pocket_y = leg_depth + clearance
    outer_x = pocket_x + 2 * wall
    outer_y = pocket_y + 2 * wall
    height = lift + pocket_depth

    body = Box(outer_x, outer_y, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Overshoot the top so the pocket opens; coplanar top faces can leave a roof.
    cutter = Box(
        pocket_x,
        pocket_y,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - cutter.move(Location((0, 0, lift)))
