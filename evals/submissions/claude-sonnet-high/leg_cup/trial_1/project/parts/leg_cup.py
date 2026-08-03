from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, clearance=0.4, draft=False):
    """
    wall: thickness of the cup's walls around the leg pocket
    pocket_depth: how far down the leg's foot drops into the pocket
    clearance: extra room around the leg so the foot slides in
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + clearance
    pocket_length = leg_depth + clearance
    outer_width = pocket_width + 2 * wall
    outer_depth = pocket_length + 2 * wall
    outer_height = lift + pocket_depth

    body = Box(outer_width, outer_depth, outer_height)
    pocket = Box(pocket_width, pocket_length, pocket_depth)
    pocket = pocket.translate((0, 0, (outer_height - pocket_depth) / 2))
    body = body - pocket

    if draft:
        return body

    bed = body.bounding_box().min.Z
    rim = body.bounding_box().max.Z
    pocket_x = pocket_width / 2
    pocket_y = pocket_length / 2

    def is_pocket_mouth(e):
        bb = e.bounding_box()
        return (
            bb.min.Z > rim - 1e-6
            and bb.min.X > -pocket_x - 1e-6
            and bb.max.X < pocket_x + 1e-6
            and bb.min.Y > -pocket_y - 1e-6
            and bb.max.Y < pocket_y + 1e-6
        )

    concave = set(concave_edges(body))
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 1e-6)
    keep = keep.filter_by(lambda e: e not in concave)
    keep = keep.filter_by(lambda e: not is_pocket_mouth(e))
    return polish(body, keep, 1.0)
