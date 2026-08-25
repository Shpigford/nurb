from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    grip_width=28.6,
    reach=34.0,
    height=14.0,
    wall=3.0,
    boss_wall=3.0,
    bore_clearance=0.6,
    draft=False,
):
    """
    shaft_diameter: diameter of the valve stem's D-shaft
    shaft_across_flat: distance across the stem through its flat
    grip_width: how wide the knob is at its narrowest, for a wet-hand grip
    reach: how far the lever tips stick out from the center
    height: how tall the knob stands
    wall: thickness of the outer shell and the bottom floor
    boss_wall: how much plastic wraps the bore inside its boss
    bore_clearance: extra room the bore gets over the stem, split between fit and no-rattle
    """
    floor = wall
    bore_depth = height - floor

    outer = SlotOverall(reach * 2.0, grip_width)
    body = extrude(outer, height)

    # D-shaped bore: a round bore with one flat, sized off both stem dimensions
    # so it both slides on and transmits torque. Flat faces +X.
    bore_radius = (shaft_diameter + bore_clearance) / 2.0
    bore_across_flat = shaft_across_flat + bore_clearance
    flat_x = bore_across_flat - bore_radius
    trim_width = bore_radius + 5.0
    trim = Pos(flat_x + trim_width / 2.0, 0) * Rectangle(trim_width, 2.0 * bore_radius + 10.0)
    bore_profile = Circle(bore_radius) - trim
    bore = Pos(0, 0, height) * extrude(bore_profile, -bore_depth)
    body = body - bore

    # Hollow the body between a thin outer shell and a boss around the bore,
    # standing on a solid floor, to keep the knob light without losing grip shape.
    boss_radius = bore_radius + boss_wall
    inner = offset(outer, -wall)
    pocket_profile = inner - Circle(boss_radius)
    pocket = Pos(0, 0, height) * extrude(pocket_profile, -bore_depth)
    body = body - pocket

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed and e not in concave
    )
    return polish(body, keep, 1.0)
