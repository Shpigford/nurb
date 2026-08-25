from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    draft=False,
):
    """Replacement D-shaft valve knob.

    shaft_diameter: round diameter of the valve stem
    shaft_across_flat: distance from the stem's round side to its +X flat
    """
    height = 16.0
    grip_radius = 14.5
    lobe_radius = 3.0
    lobe_center_radius = 14.0

    # The test stem grows each measured D dimension by 0.3 mm.  Add another
    # 0.3 mm to each opening dimension so the printed fit has real clearance.
    bore_diameter = shaft_diameter + 0.6
    bore_flat = shaft_across_flat + 0.6
    bore_radius = bore_diameter / 2.0
    bore_depth = 12.5
    bore_floor = height - bore_depth

    body = Cylinder(
        grip_radius,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for index in range(6):
        angle = index * 60.0
        lobe = Pos(
            lobe_center_radius * cos(radians(angle)),
            lobe_center_radius * sin(radians(angle)),
            0,
        ) * Cylinder(
            lobe_radius,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body + lobe

    # Intersecting a round cutter with a half-space gives a true D bore.  Its
    # clipped face is at +X, matching the stem flat orientation.
    round_cutter = Pos(0, 0, bore_floor) * Cylinder(
        bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_half_space = Pos(-20.0, -20.0, bore_floor) * Box(
        20.0 + bore_flat / 2.0,
        40.0,
        bore_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    d_cutter = round_cutter & flat_half_space
    body = body - d_cutter

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    exposed_edges = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > bed + 0.1
        and all(edge != concave_edge for concave_edge in concave)
    )
    return polish(body, exposed_edges, 0.8)
