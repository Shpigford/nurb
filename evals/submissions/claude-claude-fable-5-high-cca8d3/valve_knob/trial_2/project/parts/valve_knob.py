from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    stem_length=measured("stem_stickout"),
    bore_clearance=0.65,
    grip_width=29.0,
    lobe_size=3.2,
    knob_height=15.0,
    draft=False,
):
    """Replacement knob for the valve's D-shaft stem, printed bore-up.

    shaft_diameter: how wide the valve stem is across its round side
    shaft_across_flat: valve stem width from the flat to the round side
    stem_length: how far the stem sticks out of the valve body
    bore_clearance: total extra width in the bore over the stem, for a snug slide-on fit
    grip_width: how wide the knob body is across, not counting the lobes
    lobe_size: how far the six grip lobes bulge out from the body
    knob_height: how tall the knob is
    """
    bore_r = (shaft_diameter + bore_clearance) / 2
    flat_x = (shaft_across_flat + bore_clearance) - bore_r
    if flat_x >= bore_r - 0.3:
        reject(
            "shaft_across_flat is so close to shaft_diameter that no flat is left "
            "in the bore to grip the stem: lower it below the diameter minus 0.6",
            param="shaft_across_flat",
        )
    if flat_x <= 0.5:
        reject(
            "shaft_across_flat leaves less than half the stem: raise it past "
            f"{shaft_diameter / 2 + 0.5:.1f} so the bore keeps a real round side",
            param="shaft_across_flat",
        )
    bore_depth = stem_length + 0.5
    if knob_height < bore_depth + 2.0:
        reject(
            f"knob_height {knob_height} leaves under 2mm of floor below the "
            f"{bore_depth}mm bore: raise it past {bore_depth + 2.0}",
            param="knob_height",
        )
    if grip_width / 2 < bore_r + 4.0:
        reject(
            f"grip_width {grip_width} leaves under 4mm of wall around the "
            f"{2 * bore_r:.1f}mm bore: raise it past {2 * (bore_r + 4.0):.1f}",
            param="grip_width",
        )

    # Grip: a round core with six lobes, so wet hands get purchase.
    core_r = grip_width / 2
    profile = Circle(core_r)
    for i in range(6):
        profile += Rot(0, 0, i * 60) * Pos(core_r + 0.1, 0) * Circle(lobe_size)
    body = extrude(profile, knob_height)

    # Blind D-bore from the top face: the stem's flat faces +X.
    bore_profile = Circle(bore_r) - Pos(flat_x + bore_r, 0) * Rectangle(
        2 * bore_r, 2 * bore_r + 2
    )
    bore = Pos(0, 0, knob_height - bore_depth) * extrude(bore_profile, bore_depth)
    body -= bore

    if draft:
        return body
    # Polish the outer top rim only: the bore mouth is mating geometry and the
    # bottom face is the bed, so neither is touched.
    def outer_top(e):
        bb = e.bounding_box()
        if bb.min.Z < knob_height - 1e-6:
            return False
        return max(abs(bb.min.X), abs(bb.max.X), abs(bb.min.Y), abs(bb.max.Y)) > bore_r + 1.0

    keep = body.edges().filter_by(outer_top)
    return polish(body, keep, 1.0)
