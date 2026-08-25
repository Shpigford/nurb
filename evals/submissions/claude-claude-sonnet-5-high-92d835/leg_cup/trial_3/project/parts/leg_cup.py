from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, clearance=0.4, draft=False):
    """A slip-over cup that seats the bench's short leg and lifts it level.

    wall: thickness of the cup's side walls
    pocket_depth: how far the leg's foot drops into the pocket
    clearance: gap around the leg on each side so the foot drops in freely
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_w = leg_width + clearance
    pocket_d = leg_depth + clearance
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    total_h = lift + pocket_depth

    body = Box(outer_w, outer_d, total_h)
    body = Pos(0, 0, total_h / 2) * body

    if not draft:
        # Chamfer the plain outer box before the pocket is cut: the pocket sits
        # fully inside the 2mm walls and never reaches these edges, so doing the
        # polish pass first avoids ever selecting the pocket's mating geometry.
        # Top rim only: adding the vertical corners too would meet the rim chamfer
        # at each corner and leave a sub-1mm2 sliver triangle behind.
        top = body.bounding_box().max.Z
        keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z >= top)
        body = polish(body, keep, 1.0)

    pocket = Box(pocket_w, pocket_d, pocket_depth)
    pocket = Pos(0, 0, total_h - pocket_depth / 2) * pocket
    body -= pocket

    return body
