from nurb import *


@part
def leg_cup(fit_gap=0.4, wall_thickness=2.0, pocket_depth=8.0, corner_trim=1.0, draft=False):
    """Slip-over foot cup that levels a wobbly workbench: the short leg drops
    into the pocket from above and the solid floor under it lifts the bench.

    fit_gap: how loose the leg sits in the pocket, split across both sides
    wall_thickness: how thick the four walls around the leg are
    pocket_depth: how far the leg drops into the cup
    corner_trim: how much the four outside corners are shaved for handling
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + fit_gap
    pocket_length = leg_depth + fit_gap
    height = lift + pocket_depth

    body = Box(pocket_width + 2 * wall_thickness,
               pocket_length + 2 * wall_thickness,
               height)
    # The pocket opens straight up: cut runs 1mm past the rim so the top face
    # is opened cleanly rather than left as a coincident-face boolean.
    pocket = Pos(0, 0, lift / 2 + 0.5) * Box(pocket_width, pocket_length,
                                             pocket_depth + 1.0)
    body = body - pocket

    if draft:
        return body

    # Polish only the four full-height outside corners. The rim stays sharp:
    # its inner edge is the mating mouth and its outer edge would thin the
    # wall below wall_thickness. The bottom face is the bed. Pocket corner
    # edges are concave and never polished; they start at the pocket floor,
    # so spanning the full height excludes them.
    bb = body.bounding_box()
    corners = body.edges().filter_by(Axis.Z).filter_by(
        lambda e: e.bounding_box().min.Z < bb.min.Z + 1e-6
        and e.bounding_box().max.Z > bb.max.Z - 1e-6
    )
    return polish(body, corners, corner_trim)
