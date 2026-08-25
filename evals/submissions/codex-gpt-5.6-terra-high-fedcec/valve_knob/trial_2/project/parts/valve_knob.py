from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=16.0,
    grip_radius=14.0,
    lobe_radius=6.0,
    bore_clearance=0.7,
    draft=False,
):
    """A three-lobed replacement knob for a D-shaft valve.

    shaft_diameter: the round outside diameter of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    knob_height: overall printed height of the knob
    grip_radius: radius of the central hand-grip body
    lobe_radius: radius of each of the three turning lobes
    bore_clearance: extra diameter and flat-to-round clearance in the stem bore
    """
    if shaft_diameter <= 0.0 or shaft_across_flat <= 0.0:
        reject("The shaft dimensions must both be positive.")
    if shaft_across_flat > shaft_diameter:
        reject(
            "shaft_across_flat cannot exceed shaft_diameter.",
            param="shaft_across_flat",
        )
    if knob_height < 12.0:
        reject("knob_height must be at least 12mm for this valve stem.", param="knob_height")

    # The shaft is a circle cut by a +X-facing flat.  Clearance is applied to
    # both dimensions, preserving that non-round driving form as it scales.
    bore_diameter = shaft_diameter + bore_clearance
    bore_radius = bore_diameter / 2.0
    bore_across_flat = shaft_across_flat + bore_clearance
    flat_x = bore_across_flat - bore_radius
    bore_depth = min(knob_height - 3.0, 13.0)
    if bore_depth < 10.5:
        reject("knob_height leaves too little depth for the valve stem.", param="knob_height")
    if flat_x >= bore_radius:
        reject("shaft_across_flat makes no D-flat in the bore.", param="shaft_across_flat")

    # A compact central body carries the stem; three shallow lobes give wet
    # hands a positive turning grip without the mass of a solid large disk.
    knob = Cylinder(grip_radius, knob_height)
    lobe_center = grip_radius - 1.0
    knob += Pos(lobe_center, 0.0) * Cylinder(lobe_radius, knob_height)
    knob += Pos(-lobe_center / 2.0, lobe_center * 0.8660254) * Cylinder(lobe_radius, knob_height)
    knob += Pos(-lobe_center / 2.0, -lobe_center * 0.8660254) * Cylinder(lobe_radius, knob_height)

    # Solids are centred on the origin by default, so this puts the bore floor
    # 3mm above the printed bottom and lets it break through the top face.
    cap_center_z = knob_height / 2.0 - bore_depth / 2.0
    round_bore = Pos(0.0, 0.0, cap_center_z + 0.05) * Cylinder(
        bore_radius, bore_depth + 0.1
    )
    knob -= round_bore

    # Put back the +X cap of the round cut.  This leaves a true D bore whose
    # flat faces +X while it prints, and therefore transmits torque after use.
    cap_width = bore_radius - flat_x
    bore_cap = Pos((flat_x + bore_radius) / 2.0, 0.0, cap_center_z) * Box(
        cap_width,
        2.0 * bore_radius,
        bore_depth,
    )
    knob += bore_cap

    return knob
