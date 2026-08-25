from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=16.0,
    grip_radius=15.0,
    draft=False,
):
    """A three-lobed replacement knob for a D-shaft valve.

    shaft_diameter: diameter across the rounded sides of the valve stem
    shaft_across_flat: distance from the D-shaft flat to its rounded opposite side
    knob_height: total printed height of the knob
    grip_radius: radius of the round central grip, before the three finger lobes
    """
    if shaft_diameter <= 0.0 or shaft_across_flat <= 0.0:
        reject("shaft dimensions must be positive", param="shaft_diameter")
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )
    if knob_height < 12.5:
        reject("knob_height must be at least 12.5mm to cover the 12mm stem", param="knob_height")
    if grip_radius < 14.0:
        reject("grip_radius must be at least 14mm for a 28mm-wide hand grip", param="grip_radius")

    # A compact circular core guarantees a comfortable 30mm minimum hand span;
    # three small lobes make its maximum reach materially larger for wet fingers.
    body = Cylinder(grip_radius, knob_height)
    lobe_radius = 4.0
    lobe_center = grip_radius - 1.0
    lobe = Pos(lobe_center, 0, 0) * Cylinder(lobe_radius, knob_height)
    body = body + lobe
    body = body + (Rot(0, 0, 120.0) * lobe)
    body = body + (Rot(0, 0, 240.0) * lobe)

    # Printed clearance is 0.35mm on the rounded diameter and 0.6mm across
    # the D dimension.  The +X clipping plane is the stem's flat.
    bore_radius = shaft_diameter / 2.0 + 0.35
    bore_across_flat = shaft_across_flat + 0.60
    flat_x = -bore_radius + bore_across_flat
    bore_depth = 12.7
    round_bore = Cylinder(bore_radius, bore_depth, align=(Align.CENTER, Align.CENTER, Align.MAX))
    flat_cut = Box(bore_radius * 2.0, bore_radius * 2.0, bore_depth,
                   align=(Align.MIN, Align.CENTER, Align.MAX))
    flat_cut = Pos(flat_x, 0, 0) * flat_cut
    d_bore = round_bore & flat_cut
    result = body - d_bore

    # The bore mouth remains sharp and dimensionally stable. The lobe geometry is
    # already rounded, so an edge dress-up is not needed for the hand contact.
    return result
