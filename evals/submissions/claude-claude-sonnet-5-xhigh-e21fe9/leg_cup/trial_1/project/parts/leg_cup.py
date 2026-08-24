from nurb import *

LEG_WIDTH = measured("leg_width")
LEG_DEPTH = measured("leg_depth")
LIFT = measured("lift")


@part
def leg_cup(
    leg_width=LEG_WIDTH,
    leg_depth=LEG_DEPTH,
    lift=LIFT,
    wall=2.0,
    pocket_depth=8.0,
    clearance=0.4,
    draft=False,
):
    """A slip-over cup that raises a wobbly bench's short leg.

    leg_width: the leg's width, side to side, that drops into the pocket
    leg_depth: the leg's depth, front to back, that drops into the pocket
    lift: how much solid floor sits under the leg, raising this corner
    wall: how thick the cup's walls are around the pocket
    pocket_depth: how deep the pocket is, so the leg's foot seats fully inside it
    clearance: extra room in the pocket beyond the leg's exact measured size
    """
    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    outer_h = lift + pocket_depth

    body = Pos(0, 0, outer_h / 2) * Box(outer_w, outer_d, outer_h)
    pocket = Pos(0, 0, lift + pocket_depth / 2) * Box(pocket_w, pocket_d, pocket_depth)
    body -= pocket

    if draft:
        return body

    # Standing vetoes: nothing lying in the bottom face (first layer) and nothing
    # concave (the pocket's own rim and floor corners, which would wedge if polished).
    # The vertical outer corners are excluded too: chamfering them together with the
    # top rim leaves three chamfers meeting at each of the 4 top corners, a sub-mm2
    # sliver triangle. The rim carries the polish and the corners stay sharp instead.
    top = body.bounding_box().max.Z
    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > top - 1e-6 and e not in concave
    )
    return polish(body, keep, 1.0)
