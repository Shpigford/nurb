from nurb import *


@part
def leg_cup(fit_gap=0.4, wall_thickness=2.0, pocket_depth=8.0, draft=False):
    """A slip-over cup: the bench leg's foot drops in, the solid floor lifts it level.

    fit_gap: how much wider the pocket is than the leg, so the foot drops in
    wall_thickness: how thick the four walls around the leg are
    pocket_depth: how far the leg's foot sits down into the cup
    """
    leg_w = measured("leg_width")
    leg_d = measured("leg_depth")
    lift = measured("lift")

    pocket_w = leg_w + fit_gap
    pocket_d = leg_d + fit_gap
    outer_w = pocket_w + 2 * wall_thickness
    outer_d = pocket_d + 2 * wall_thickness
    height = lift + pocket_depth

    body = Box(outer_w, outer_d, height)

    if not draft:
        # Only the four outer vertical corners: they stand square to the plate, so the
        # first layer keeps its full width. The rim is a mating mouth and stays sharp.
        corners = body.edges().filter_by(Axis.Z)
        body = polish(body, corners, 1.0)

    # Pocket opens straight up out of the solid floor, nothing roofing it over.
    pocket = Pos(0, 0, (height - pocket_depth) / 2) * Box(pocket_w, pocket_d, pocket_depth)
    return body - pocket
