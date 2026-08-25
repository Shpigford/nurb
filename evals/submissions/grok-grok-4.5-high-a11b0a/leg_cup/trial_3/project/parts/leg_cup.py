from nurb import *

# Fit constants that are not measurements: print clearance and cup geometry.
_CLEARANCE = 0.4
_WALL = 2.0
_POCKET_DEPTH = 8.0


@part
def leg_cup(draft=False):
    """Slip-over foot cup that seats a short workbench leg and lifts it level.

    Pocket and lift come from measurements.toml (leg_width, leg_depth, lift).
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_w = leg_width + _CLEARANCE
    pocket_d = leg_depth + _CLEARANCE
    outer_w = pocket_w + 2 * _WALL
    outer_d = pocket_d + 2 * _WALL
    outer_h = lift + _POCKET_DEPTH

    body = Box(outer_w, outer_d, outer_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pocket = Box(
        pocket_w,
        pocket_d,
        _POCKET_DEPTH,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).translate((0, 0, lift))
    body = body - pocket

    if draft:
        return body

    # Flat bed face stays sharp. Concave and pocket-mouth edges stay sharp (fit).
    # Polish only exposed convex edges that sit fully above the bed.
    bed = body.bounding_box().min.Z
    forbidden = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6 and e not in forbidden
    )
    return polish(body, keep, 1.0)
