from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup for a short workbench leg.

    The leg drops into an open rectangular pocket from above; the solid floor
    under the pocket lifts the bench by `lift`. Leg section and lift come from
    measurements.toml (leg_width, leg_depth, lift) so rebuilt geometry tracks
    that file. Pocket clearance 0.4, walls 2.0, pocket depth 8.0 are design
    constants. Mating pocket edges stay sharp; no polish, so the bounding box
    and volume match the stated walls and floor exactly.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0

    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2.0 * wall
    outer_d = pocket_d + 2.0 * wall
    outer_h = lift + pocket_depth

    body = Box(outer_w, outer_d, outer_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Overcut past the rim so the pocket opens fully with nothing roofing it.
    pocket = Box(
        pocket_w,
        pocket_d,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).move(Location((0, 0, lift)))
    return body - pocket
