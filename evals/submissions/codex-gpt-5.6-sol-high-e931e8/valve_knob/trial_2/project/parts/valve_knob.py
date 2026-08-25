from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=14.0,
    draft=False,
):
    """A low-profile, six-lobed replacement knob for a D-shaped valve stem.

    shaft_diameter: diameter of the round portion of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    knob_height: overall printed height of the knob
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )
    if knob_height < 12.0:
        reject("knob_height must be at least 12 mm", param="knob_height")

    core_radius = 15.0
    lobe_radius = 4.0
    lobe_center_radius = 15.0

    vertical = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Cylinder(core_radius, knob_height, align=vertical)
    for angle in range(0, 360, 60):
        x = lobe_center_radius * cos(radians(angle))
        y = lobe_center_radius * sin(radians(angle))
        body += Pos(x, y, 0) * Cylinder(
            lobe_radius, knob_height, align=vertical
        )

    if not draft:
        bed = body.bounding_box().min.Z
        top_edges = body.edges().filter_by(
            lambda edge: edge.bounding_box().min.Z > bed
        )
        body = polish(body, top_edges, 1.0)

    # The 0.5 mm diametral allowance lies between the +0.3 mm pass gauge and
    # the +1.0 mm jam gauge. The same allowance on the across-flat dimension
    # preserves the D profile and therefore transmits torque.
    bore_allowance = 0.5
    bore_diameter = shaft_diameter + bore_allowance
    bore_across_flat = shaft_across_flat + bore_allowance
    bore_radius = bore_diameter / 2.0
    flat_x = bore_across_flat - bore_radius
    bore_depth = 10.5
    bore_floor = knob_height - bore_depth

    round_bore = Pos(0, 0, bore_floor) * Cylinder(
        bore_radius, bore_depth + 0.5, align=vertical
    )
    clip_width = flat_x + bore_radius
    clip_center_x = (flat_x - bore_radius) / 2.0
    flat_clip = Pos(clip_center_x, 0, bore_floor) * Box(
        clip_width,
        bore_diameter + 1.0,
        bore_depth + 0.5,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore & flat_clip

    return body - d_bore
