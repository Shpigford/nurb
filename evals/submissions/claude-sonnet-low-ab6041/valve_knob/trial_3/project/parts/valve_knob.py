from nurb import *
from math import cos, sin, radians


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    height=16.0,
    base_radius=14.1,
    lobe_radius=3.5,
    lobe_count=3,
    bore_depth=13.0,
    bore_clearance=0.6,
    draft=False,
):
    """
    shaft_diameter: diameter of the valve stem's round side
    shaft_across_flat: distance across the stem from its flat to the opposite round edge
    height: how tall the knob stands
    base_radius: radius of the knob's round body, sets the narrowest grip width
    lobe_radius: size of each grip bump on the rim, for a wet-hand grip
    lobe_count: how many grip bumps around the knob
    bore_depth: how deep the stem socket cuts into the knob
    bore_clearance: extra room the socket gets over the stem so it slips on and off
    """
    lobe_offset = base_radius

    profile = Circle(base_radius)
    for i in range(lobe_count):
        angle = 360.0 / lobe_count * i + 90.0
        cx = lobe_offset * cos(radians(angle))
        cy = lobe_offset * sin(radians(angle))
        profile = profile + Pos(cx, cy) * Circle(lobe_radius)

    body = extrude(profile, height)

    bore_dia = shaft_diameter + bore_clearance
    bore_flat = shaft_across_flat + bore_clearance
    r = bore_dia / 2
    flat_offset = bore_flat - r
    bore_profile = Circle(r) - Pos(flat_offset + r, 0) * Rectangle(2 * r, 4 * r)
    bore = extrude(bore_profile, bore_depth).translate((0, 0, height - bore_depth))

    knob = body - bore

    if draft:
        return knob

    bed = knob.bounding_box().min.Z
    concave = set(concave_edges(knob))
    keep = knob.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(knob, keep, 1.0)
