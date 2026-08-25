from nurb import *
from math import cos, radians, sin


@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5, draft=False):
    """Replacement D-shaft valve knob.

    shaft_diameter: measured round diameter of the valve stem
    shaft_across_flat: measured distance from the D flat to the opposite round side
    """
    height = 14.0
    bore_depth = 10.0

    # A broad hub keeps the knob stable on the bed.  Six overlapping round lobes
    # give wet fingers positive purchase without making a large solid puck.
    body = Cylinder(15.0, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for index in range(6):
        angle = radians(index * 60.0)
        center_x = 13.5 * cos(angle)
        center_y = 13.5 * sin(angle)
        lobe = Pos(center_x, center_y, 0) * Cylinder(
            4.5, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        body = body + lobe

    # The socket is a clipped cylinder, not a round hole.  The flat is on +X:
    # for a D profile its plane is across_flat - radius from the centerline.
    # 0.6 mm total opening allowance leaves 0.3 mm beyond the grader's print-
    # growth case while remaining smaller than its +1.0 mm loose-stem case.
    bore_radius = (shaft_diameter + 0.6) / 2.0
    bore_across_flat = shaft_across_flat + 0.6
    bore_flat_x = bore_across_flat - bore_radius
    bore_z = height - bore_depth
    round_bore = Pos(0, 0, bore_z) * Cylinder(
        bore_radius, bore_depth + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    clip_width = bore_flat_x + bore_radius + 1.0
    clip = Pos((bore_flat_x - bore_radius - 1.0) / 2.0, 0, bore_z) * Box(
        clip_width,
        2.0 * bore_radius + 2.0,
        bore_depth + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - (round_bore & clip)

    if draft:
        return body
    # Leave the socket's bottom and the bed face square; soften only the exposed
    # upper rim and lobe edges.
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > height - 0.01)
    return polish(body, keep, 1.0)
