from nurb import *


@part
def leg_cup(
    leg_width=measured("leg_width"),
    leg_depth=measured("leg_depth"),
    lift=measured("lift"),
    foot_clearance=0.4,
    pocket_depth=8.0,
    wall_thickness=2.0,
    draft=False,
):
    """A slip-over foot cup: the bench leg drops in from above and the solid floor lifts it level.

    leg_width: the wide side of the bench leg the pocket has to swallow
    leg_depth: the narrow side of the bench leg the pocket has to swallow
    lift: how much taller the short leg has to stand, which is the floor thickness
    foot_clearance: total slop across the pocket so the leg slips on without forcing
    pocket_depth: how far up the leg the cup grips
    wall_thickness: how thick each of the four walls around the leg is
    """
    pocket_width = leg_width + foot_clearance
    pocket_breadth = leg_depth + foot_clearance
    outer_width = pocket_width + 2 * wall_thickness
    outer_breadth = pocket_breadth + 2 * wall_thickness
    total_height = lift + pocket_depth

    body = Pos(0, 0, total_height / 2) * Box(outer_width, outer_breadth, total_height)

    # The pocket opens straight up, so the cut runs clear out through the rim: nothing
    # roofs it over and the mouth stays the full pocket size.
    overshoot = pocket_depth + 5.0
    body -= Pos(0, 0, lift + overshoot / 2) * Box(
        pocket_width, pocket_breadth, overshoot
    )

    if draft:
        return body

    # Name what must stay sharp, then let `polish` chamfer whatever the kernel takes.
    # A bare `chamfer(...)` is all or nothing: one edge that cannot land loses the lot.
    tol = 1e-6
    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))

    def in_pocket(edge):
        # Everything at or inside the pocket walls is mating geometry: the mouth, the
        # four inner corners, the floor. A lead-in chamfer there is exactly what the
        # doctrine forbids.
        box = edge.bounding_box()
        return (
            max(abs(box.min.X), abs(box.max.X)) <= pocket_width / 2 + 0.01
            and max(abs(box.min.Y), abs(box.max.Y)) <= pocket_breadth / 2 + 0.01
        )

    rim = body.bounding_box().max.Z

    def keepable(edge):
        box = edge.bounding_box()
        if box.max.Z <= bed + tol:  # lies in the bed-contact face
            return False
        if box.min.Z >= rim - tol:  # lies in the rim face, see below
            return False
        if in_pocket(edge):
            return False
        return edge not in concave

    # That leaves the four vertical corners, the most-handled edges on the part, and
    # nothing else. The rim ring stays sharp on purpose: it is only 2mm wide, so a
    # chamfer there spends half the wall at the mouth that does the gripping, and where
    # it met the corner chamfers it would leave a sliver triangle at every corner.

    keep = body.edges().filter_by(keepable)
    return polish(body, keep, 1.0)
