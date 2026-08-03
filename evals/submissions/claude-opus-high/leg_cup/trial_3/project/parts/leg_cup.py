from nurb import *


@part
def leg_cup(foot_gap=0.4, wall_thickness=2.0, pocket_depth=8.0, draft=False):
    """A cup the short bench leg stands in, with a solid floor that lifts it level.

    foot_gap: how much wider than the leg the pocket is, so the foot drops in by hand
    wall_thickness: how thick the four walls that wrap the leg are
    pocket_depth: how far down into the cup the foot sits
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + foot_gap
    pocket_length = leg_depth + foot_gap
    outer_width = pocket_width + 2 * wall_thickness
    outer_length = pocket_length + 2 * wall_thickness
    height = lift + pocket_depth

    body = Box(outer_width, outer_length, height)
    # Cut from above and run the cutter out through the roof: the pocket opens straight
    # up, and what is left under it is the lift.
    body -= Pos(0, 0, height / 2) * Box(pocket_width, pocket_length, 2 * pocket_depth)

    if draft:
        return body

    box = body.bounding_box()
    bed, rim = box.min.Z, box.max.Z
    concave = set(concave_edges(body))

    def in_pocket(edge):
        # An edge of the pocket: the leg slides against it, so it stays sharp.
        eb = edge.bounding_box()
        return (
            eb.min.X >= -pocket_width / 2 - 1e-6
            and eb.max.X <= pocket_width / 2 + 1e-6
            and eb.min.Y >= -pocket_length / 2 - 1e-6
            and eb.max.Y <= pocket_length / 2 + 1e-6
            and eb.min.Z >= rim - pocket_depth - 1e-6
        )

    def upright(edge):
        eb = edge.bounding_box()
        return eb.min.Z < bed + 1e-6 and eb.max.Z > rim - 1e-6

    # The four outer corners and nothing else. They stand square to the plate, so their
    # chamfers print full width, and being alone they meet no other chamfer to sliver
    # against. The rim above them stays a full 2mm wall; see the card.
    keep = body.edges().filter_by(
        lambda e: upright(e) and e not in concave and not in_pocket(e)
    )
    return polish(body, keep, 1.0)
