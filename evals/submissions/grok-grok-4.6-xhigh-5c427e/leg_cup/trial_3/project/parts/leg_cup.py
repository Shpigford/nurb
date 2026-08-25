from nurb import *

# Fit slack and wall are specified, not measured: the pocket is the leg plus 0.4 mm
# so it slips on, walls are 2 mm all round, and the pocket is 8 mm deep.
_CLEARANCE = 0.4
_WALL = 2.0
_POCKET_DEPTH = 8.0


@part
def leg_cup(draft=False):
    """Slip-over foot cup that lifts a short workbench leg until the bench sits level.

    The cup sits on the floor; the leg drops into the pocket from above. Floor thickness
    under the foot is lift, read from measurements.toml, not a baked-in number.

    Geometry is derived only from leg_width, leg_depth, and lift.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_w = leg_width + _CLEARANCE
    pocket_d = leg_depth + _CLEARANCE
    outer_w = pocket_w + 2 * _WALL
    outer_d = pocket_d + 2 * _WALL
    height = lift + _POCKET_DEPTH

    body = Box(outer_w, outer_d, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Overshoot the top so the cut cannot leave a film on coplanar faces.
    cut = Box(
        pocket_w,
        pocket_d,
        _POCKET_DEPTH + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cup = body - cut.move(Location((0, 0, lift)))

    if draft:
        return cup

    # Mating pocket, concave floor corners, and the bed face stay sharp. The 2 mm
    # rim cannot take a 1 mm chamfer on both inner and outer edges, and the inner
    # rim is the slip-over mouth, so polish only the four outer vertical corners.
    bb = cup.bounding_box()
    tol = 1e-4

    def outer_corner(edge):
        c = edge.center()
        on_x = abs(c.X - bb.min.X) < tol or abs(c.X - bb.max.X) < tol
        on_y = abs(c.Y - bb.min.Y) < tol or abs(c.Y - bb.max.Y) < tol
        return on_x and on_y

    keep = cup.edges().filter_by(Axis.Z).filter_by(outer_corner)
    return polish(cup, keep, 1.0)
