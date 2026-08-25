from nurb import *


@part
def leg_cup(draft=False):
    """Slip-over foot cup: short workbench leg drops in from above; solid floor lifts it level.

    Geometry is driven only by measured leg_width, leg_depth, and lift.
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    clearance = 0.4
    wall = 2.0
    pocket_depth = 8.0

    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    outer_h = lift + pocket_depth

    body = Box(outer_w, outer_d, outer_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Overshoot the rim so the cut leaves an open pocket of exactly pocket_depth.
    pocket = Box(
        pocket_w,
        pocket_d,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).move(Location((0, 0, lift)))
    cup = body - pocket

    if draft:
        return cup

    # Polish only the four outer vertical corners. Pocket rim is fit-critical;
    # edges lying in the bed stay sharp; concave pocket edges are never polished.
    bed = cup.bounding_box().min.Z
    top = cup.bounding_box().max.Z
    forbidden = set(concave_edges(cup))

    def is_outer_vertical(edge):
        if edge in forbidden:
            return False
        bb = edge.bounding_box()
        # Skip edges that lie in the bed face.
        if bb.size.Z < 1e-4 and bb.min.Z <= bed + 1e-4:
            return False
        # Full-height vertical corner: spans nearly bed→top, negligible XY length.
        if bb.size.Z < (top - bed) - 0.5:
            return False
        if bb.size.X > 0.1 or bb.size.Y > 0.1:
            return False
        return True

    keep = [e for e in cup.edges() if is_outer_vertical(e)]
    if not keep:
        return cup
    return polish(cup, keep, 1.0)
