from nurb import *


@part
def pole_rest(pole_diameter=20.0, length=20.0, draft=False):
    """A low, open-top drying cradle for a finished round pole.

    pole_diameter: measured diameter of the pole the rest supports
    length: how far the rest runs along the pole

    The pole axis is deliberately fixed at Z=18.0. The through-cut is a
    slightly oversized horizontal cylinder: its lower 180 degrees form a
    broad, backed cradle while its upper half remains completely open for a
    vertical drop-in.
    """
    axis_height = 18.0
    clearance = 0.2
    cradle_radius = pole_diameter / 2.0 + clearance
    backing = 1.5
    width = 2.0 * (cradle_radius + backing)

    body = Box(
        width,
        length,
        axis_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bore = Cylinder(
        cradle_radius,
        length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).rotate(Axis.X, 90).translate((0, 0, axis_height))
    return body - bore
