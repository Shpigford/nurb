from nurb import *

@part
def leg_cup(draft=False):
    """Slip-over foot cup that fixes a wobbly workbench.

    The cup lifts and stabilizes the bench leg, which slides down into
    the open pocket from above.
    """
    leg_w = measured("leg_width")  # 22.0 mm
    leg_d = measured("leg_depth")  # 18.5 mm
    lft = measured("lift")  # provisional, between 2.0 and 5.0

    wall = 2.0
    pocket_height = 8.0
    clearance = 0.4

    pocket_w = leg_w + clearance  # 22.4 mm
    pocket_d = leg_d + clearance  # 18.9 mm

    outer_w = pocket_w + 2 * wall  # 26.4 mm
    outer_d = pocket_d + 2 * wall  # 22.9 mm
    total_h = lft + pocket_height

    # Start with full outer box
    body = Box(outer_w, outer_d, total_h)

    # Cut the pocket from the top: it sits 8.0 deep, leaving the lift floor solid
    # The outer box is centered, so it goes from z = -total_h/2 to +total_h/2
    # We want the pocket floor at z = -total_h/2 + lft
    # A centered pocket box goes from z = -pocket_height/2 to +pocket_height/2
    # So we translate by: (-total_h/2 + lft) - (-pocket_height/2) = (pocket_height - total_h)/2 + lft
    pocket = Box(pocket_w, pocket_d, pocket_height)
    pocket_offset = lft - total_h / 2 + pocket_height / 2
    pocket = pocket.translate((0, 0, pocket_offset))
    body = body - pocket

    if draft:
        return body

    # Polish exposed edges, excluding concave edges (which collect stress)
    bed = body.bounding_box().min.Z
    concave = concave_edges(body)

    # Edges above the bed but not concave
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 0.01)
    keep = keep - concave

    return polish(body, keep, 1.0)
