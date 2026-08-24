from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, fit_clearance=0.4, draft=False):
    """A slip-over foot cup that levels the wobbly workbench.

    wall: how thick the cup's sides are around the leg
    pocket_depth: how far the leg's foot drops into the cup
    fit_clearance: total extra width in the pocket so the leg slides in
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_w = leg_width + fit_clearance
    pocket_d = leg_depth + fit_clearance
    outer_w = pocket_w + 2 * wall
    outer_d = pocket_d + 2 * wall
    height = lift + pocket_depth

    body = Pos(0, 0, height / 2) * Box(outer_w, outer_d, height)
    # Cut past the rim so the boolean never leaves a coplanar membrane over the mouth.
    pocket = Pos(0, 0, lift + (pocket_depth + 1) / 2) * Box(
        pocket_w, pocket_d, pocket_depth + 1
    )
    body = body - pocket

    if draft:
        return body

    # Polish only the four outer vertical corners. The pocket is fit-critical mating
    # geometry so its rim stays sharp, edges lying in the bed face are never
    # chamfered, and a rim chamfer on the 2mm wall meeting the corner chamfers
    # leaves sliver cap faces, so the top edges stay square too.
    def outer_vertical_corner(e):
        bb = e.bounding_box()
        return (
            max(abs(bb.min.X), abs(bb.max.X)) > outer_w / 2 - 0.01
            and max(abs(bb.min.Y), abs(bb.max.Y)) > outer_d / 2 - 0.01
            and bb.max.Z - bb.min.Z > 0.01
        )

    keep = body.edges().filter_by(outer_vertical_corner)
    return polish(body, keep, 1.0)
