from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=14.0,
    hub_diameter=30.0,
    lever_reach=35.0,
    lever_width=14.0,
    bore_clearance=0.8,
    bore_depth=12.0,
    draft=False,
):
    """
    shaft_diameter: full round diameter of the valve's D-shaft
    shaft_across_flat: distance across the D-shaft from its flat to the round side
    knob_height: how tall the knob stands off the bed
    hub_diameter: width of the round grip hub, across its unflatted sides
    lever_reach: how far the turning lever reaches from the centerline
    lever_width: width of the turning lever
    bore_clearance: total extra added to the shaft's diameter and across-flat for the bore
    bore_depth: how deep the bore cuts down from the top face
    """
    hub_r = hub_diameter / 2.0
    bore_dia = shaft_diameter + bore_clearance
    bore_af = shaft_across_flat + bore_clearance
    bore_r = bore_dia / 2.0
    flat_offset = bore_af - bore_r

    tip_y = lever_reach - lever_width / 2.0
    hub = Circle(hub_r)
    lever_rect = Pos(0, tip_y / 2.0) * Rectangle(lever_width, tip_y)
    lever_cap = Pos(0, tip_y) * Circle(lever_width / 2.0)
    profile = hub + lever_rect + lever_cap

    body = extrude(profile, knob_height)

    cut_half = bore_r + 1.0
    bore_2d = Circle(bore_r) - Pos(flat_offset + cut_half, 0) * Rectangle(2 * cut_half, 2 * cut_half)
    bore_solid = Pos(0, 0, knob_height - bore_depth) * extrude(bore_2d, bore_depth)

    knob = body - bore_solid

    if draft:
        return knob

    concave = set(concave_edges(knob))
    top_z = knob_height
    top_edges = knob.edges().filter_by(
        lambda e: abs(e.bounding_box().min.Z - top_z) < 1e-6
        and abs(e.bounding_box().max.Z - top_z) < 1e-6
    )

    def is_outer(e):
        c = e.center()
        return (c.X ** 2 + c.Y ** 2) ** 0.5 > bore_r + 3.0

    keep = top_edges.filter_by(is_outer).filter_by(lambda e: e not in concave)

    return polish(knob, keep, 1.0)
