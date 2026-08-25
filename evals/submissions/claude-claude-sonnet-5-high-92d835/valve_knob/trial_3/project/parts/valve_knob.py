from math import cos, radians, sin

from nurb import *


@part
def valve_knob(shaft_diameter=8.0, shaft_across_flat=6.5, draft=False):
    """
    shaft_diameter: diameter of the valve stem, measured across the round
    shaft_across_flat: distance across the stem, from its flat side to the round side opposite
    """
    if not (0.0 < shaft_across_flat < shaft_diameter):
        reject(
            f"shaft_across_flat {shaft_across_flat} has to sit strictly between 0 and "
            f"shaft_diameter {shaft_diameter} for a D-shaft flat to make sense",
            param="shaft_across_flat",
        )

    height = 13.0
    bore_depth = 11.0
    core_radius = 15.0
    lobe_radius = 7.0
    lobe_offset = 13.0
    fit_extra = 0.65  # opening over the true stem: clears a +0.3 grown stem, jams a +1.0 one

    grip = Circle(core_radius)
    for i in range(3):
        angle = radians(i * 120.0)
        grip += Pos(lobe_offset * cos(angle), lobe_offset * sin(angle)) * Circle(lobe_radius)
    body = extrude(grip, height)

    bore_radius = (shaft_diameter + fit_extra) / 2.0
    flat_x = (shaft_across_flat + fit_extra) - bore_radius
    trim_width = 2.0 * bore_radius + 4.0
    trim = Pos(flat_x + trim_width / 2.0, 0) * Rectangle(trim_width, trim_width)
    bore_face = Circle(bore_radius) - trim
    bore = Pos(0, 0, height - bore_depth) * extrude(bore_face, bore_depth)

    knob = body - bore
    if draft:
        return knob

    bed = knob.bounding_box().min.Z
    concave = concave_edges(knob)
    keep = knob.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(knob, keep, 1.0)
