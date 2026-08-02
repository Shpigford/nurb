from nurb import *


@part
def leg_cup(wall=2.0, pocket_depth=8.0, slip_room=0.4, draft=False):
    """A slip-over cup for the workbench's short leg.

    wall: how thick the cup's sides are
    pocket_depth: how deep the leg's foot drops into the cup
    slip_room: extra width in the pocket so the cup slips on without forcing
    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + slip_room
    pocket_length = leg_depth + slip_room
    outer_width = pocket_width + 2 * wall
    outer_length = pocket_length + 2 * wall
    height = lift + pocket_depth

    body = Box(
        outer_width,
        outer_length,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pocket = Pos(0, 0, lift) * Box(
        pocket_width,
        pocket_length,
        pocket_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - pocket

    if draft:
        return body

    # Polish only the four outer vertical corners. The pocket mouth is mating
    # geometry, the bottom is the bed face, and the rim must stay full width
    # to the top to seat the leg, so top and inner edges all stay sharp.
    corners = (
        body.edges()
        .filter_by(Axis.Z)
        .filter_by(
            lambda e: abs(abs(e.center().X) - outer_width / 2) < 1e-6
            and abs(abs(e.center().Y) - outer_length / 2) < 1e-6
        )
    )
    return polish(body, corners, 1.0)
