from nurb import *

CLEARANCE = 0.4
WALL = 2.0
POCKET_DEPTH = 8.0


@part
def leg_cup(draft=False):
    """Slip-over cup that sits on the floor and lifts a short workbench leg level.

    The rectangular pocket takes the leg from above; the solid floor under the foot is
    the lift. Width, depth, and lift all come from measurements.toml so an updated
    lift rebuilds the floor without touching this file.

    """
    leg_width = measured("leg_width")
    leg_depth = measured("leg_depth")
    lift = measured("lift")

    pocket_width = leg_width + CLEARANCE
    pocket_span = leg_depth + CLEARANCE
    outer_width = pocket_width + 2 * WALL
    outer_span = pocket_span + 2 * WALL
    height = lift + POCKET_DEPTH

    body = Box(
        outer_width,
        outer_span,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Overcut the open top so the boolean cannot leave a film over the pocket.
    cavity = Box(
        pocket_width,
        pocket_span,
        POCKET_DEPTH + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cavity = cavity.move(Location((0, 0, lift)))
    cup = body - cavity
    if draft:
        return cup
    # Mating pocket and 2 mm walls: a 1 mm polish on both rim edges cannot land,
    # and the pocket mouth must stay the modelled size. Bed stays sharp for grip.
    return cup
