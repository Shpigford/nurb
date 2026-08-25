from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """Replacement knob for the measured D-shaped valve stem.

    shaft_diameter: diameter of the round portion of the valve stem
    shaft_across_flat: distance from the round back of the stem to its flat
    """
    height = 16.0
    grip_radius = 15.0
    lobe_radius = 4.0
    lobe_circle_radius = 14.0

    body = Cylinder(
        grip_radius,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for angle in range(0, 360, 60):
        x = lobe_circle_radius * cos(radians(angle))
        y = lobe_circle_radius * sin(radians(angle))
        body = body + Pos(x, y, 0) * Cylinder(
            lobe_radius,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    # Leave clearance for the specified +0.3mm fit check while retaining the
    # larger +1.0mm no-rattle check as an intentional interference fit.
    bore_radius = shaft_diameter / 2.0 + 0.45
    bore_across_flat = shaft_across_flat + 0.80
    bore_flat_x = -bore_radius + bore_across_flat
    bore_depth = 12.0
    bore_bottom = height - bore_depth

    round_bore = Pos(0, 0, bore_bottom) * Cylinder(
        bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_clip = Pos((bore_flat_x - bore_radius) / 2.0, 0, bore_bottom) * Box(
        bore_flat_x + bore_radius,
        2.0 * bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore & flat_clip
    body = body - d_bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    exposed = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > height - 0.01 and e not in concave
    )
    return polish(body, exposed, 1.0)
