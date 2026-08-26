from nurb import *


@part
def leg_cup(
    leg_clearance=0.4,
    pocket_depth=8.0,
    wall_thickness=2.0,
    corner_chamfer=1.0,
    rim_chamfer=0.8,
    draft=False,
):
    """A slip-over cup for the workbench's short leg: the foot drops into the
    pocket from above and the solid floor underneath lifts the bench level.

    leg_clearance: total slack across the pocket, so the leg slips in without forcing
    pocket_depth: how far the leg's foot sinks into the cup
    wall_thickness: how thick the four walls around the leg are
    corner_chamfer: how much is taken off the four upright outside corners
    rim_chamfer: how much is taken off the outside edge of the rim
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_x = leg_width + leg_clearance
    pocket_y = leg_depth + leg_clearance
    outer_x = pocket_x + 2 * wall_thickness
    outer_y = pocket_y + 2 * wall_thickness
    height = lift + pocket_depth

    body = Pos(0, 0, height / 2) * Box(outer_x, outer_y, height)

    # Cut from the floor straight out through the top, so the pocket is open
    # upward and its floor is the only thing under the foot.
    overshoot = 1.0
    pocket = Pos(0, 0, lift + (pocket_depth + overshoot) / 2) * Box(
        pocket_x, pocket_y, pocket_depth + overshoot
    )
    body = body - pocket

    if draft:
        return body

    # Only the outside gets polished. The pocket rim stays sharp: chamfering both
    # sides of a 2mm wall would run it out to a knife edge at the top.
    half_x, half_y = outer_x / 2, outer_y / 2

    def on_outer_wall(edge):
        bb = edge.bounding_box()
        return (
            abs(abs(bb.min.X) - half_x) < 1e-6 and abs(abs(bb.max.X) - half_x) < 1e-6
        ) or (abs(abs(bb.min.Y) - half_y) < 1e-6 and abs(abs(bb.max.Y) - half_y) < 1e-6)

    uprights = body.edges().filter_by(
        lambda e: on_outer_wall(e)
        and e.bounding_box().max.Z - e.bounding_box().min.Z > 1e-6
    )
    body = polish(body, uprights, corner_chamfer)
    rim = body.edges().filter_by(
        lambda e: on_outer_wall(e)
        and abs(e.bounding_box().min.Z - (lift + pocket_depth)) < 1e-6
        and abs(e.bounding_box().max.Z - (lift + pocket_depth)) < 1e-6
    )
    return polish(body, rim, rim_chamfer)
