from nurb import *
from math import cos, radians, sin


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """A support-free, six-lobed replacement knob for a D-shaft valve.

    shaft_diameter: round diameter of the valve stem
    shaft_across_flat: distance from the stem's round side to its flat
    """
    height = 16.0
    body_radius = 14.0
    lobe_radius = 4.0
    lobe_center_radius = 13.5

    # The bore is a D, not a round hole: the flat is on +X.  The same
    # clearance is applied to the round diameter and to the across-flat
    # measurement so both fit and torque remain driven by the shaft inputs.
    bore_clearance = 0.4
    shaft_radius = shaft_diameter / 2.0
    shaft_flat_x = shaft_across_flat - shaft_radius
    bore_radius = shaft_radius + bore_clearance
    bore_flat_x = shaft_flat_x + bore_clearance
    bore_depth = 12.0
    bore_bottom = height - bore_depth

    align_min = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Cylinder(body_radius, height, align=align_min)
    for angle in range(0, 360, 60):
        lobe = Pos(
            lobe_center_radius * cos(radians(angle)),
            lobe_center_radius * sin(radians(angle)),
            0,
        ) * Cylinder(lobe_radius, height, align=align_min)
        body = body + lobe

    # Intersect the round bore with a half-space ending at the +X flat.
    round_bore = Pos(0, 0, bore_bottom) * Cylinder(
        bore_radius, bore_depth, align=align_min
    )
    flat_half_space = Pos(bore_flat_x - 20.0, 0, bore_bottom) * Box(
        40.0, 40.0, bore_depth, align=align_min
    )
    d_bore = round_bore & flat_half_space
    body = body - d_bore

    if draft:
        return body

    # Keep the bed edge crisp and soften the exposed top perimeter.
    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(body, keep, 1.0)
