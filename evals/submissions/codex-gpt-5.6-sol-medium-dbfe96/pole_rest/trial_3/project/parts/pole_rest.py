import math

from nurb import *


@part
def pole_rest(pole_diameter: float = measured("pole_diameter")):
    """A low circular cradle for supporting a freshly finished pole.

    pole_diameter: measured diameter of the pole resting in the cradle
    """
    axis_height = 18.0
    length = 24.0
    base_width = 28.0
    radial_clearance = 0.2

    pole_radius = pole_diameter / 2.0
    inner_radius = pole_radius + radial_clearance

    # Provide 144 degrees before edge finishing so more than the required
    # continuous 120-degree pole-matching surface remains. The whole seat is
    # below the axis, leaving the approach from above unobstructed.
    half_arc = 72.0
    saddle_top = axis_height - inner_radius * math.cos(math.radians(half_arc))

    blank = Box(
        base_width,
        length,
        saddle_top,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    cavity = Cylinder(
        inner_radius,
        length + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).rotate(Axis.X, 90).translate((0, 0, axis_height))
    body = blank - cavity

    bed = body.bounding_box().min.Z
    exposed_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > bed + 0.01
        and edge.bounding_box().size.Y > length - 0.1
        and abs(edge.center().X) > base_width / 2.0 - 0.01
    )
    return polish(body, exposed_edges, 0.8)
