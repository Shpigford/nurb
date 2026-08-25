from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    knob_height=16.0,
    core_radius=14.0,
    lobe_radius=6.0,
    bore_clearance=0.8,
    draft=False,
):
    """A three-lobed replacement valve knob for an upright D-shaped stem.

    shaft_diameter: measured diameter across the round sides of the stem
    shaft_across_flat: measured distance from the flat to the opposite round side
    knob_height: overall printed height of the knob
    core_radius: radius between the grip lobes
    lobe_radius: roundness and reach of each grip lobe
    bore_clearance: total extra opening on both D-shaft measurements
    """
    if shaft_diameter <= 2.0:
        reject("shaft_diameter must be over 2.0mm", param="shaft_diameter")
    if shaft_across_flat <= 2.0 or shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be between 2.0mm and shaft_diameter",
            param="shaft_across_flat",
        )
    if knob_height < 14.0:
        reject("knob_height must leave a 12.0mm stem socket and 2.0mm base", param="knob_height")

    # The bore is modelled in its print orientation: open upward, with its flat at +X.
    # Adding clearance to both defining D-shaft dimensions preserves that flat rather
    # than turning the fit into a torque-free round hole.
    bore_diameter = shaft_diameter + bore_clearance
    bore_across_flat = shaft_across_flat + bore_clearance
    bore_radius = bore_diameter / 2.0
    bore_flat_x = -bore_radius + bore_across_flat
    base_thickness = 3.0
    bore_depth = knob_height - base_thickness

    body = Cylinder(core_radius, knob_height)
    for angle in (0.0, 120.0, 240.0):
        lobe_center = Pos(core_radius - 3.0, 0, 0) * Cylinder(lobe_radius, knob_height)
        body += lobe_center.rotate(Axis.Z, angle)

    round_bore = Pos(0, 0, base_thickness) * Cylinder(bore_radius, bore_depth)
    # Remove the +X cap of the circle. Its inner face is the D-shaft's torque flat.
    flat_cut = Pos(bore_flat_x + bore_radius / 2.0, 0, base_thickness) * Box(
        bore_radius,
        bore_diameter + 2.0,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bore = round_bore - flat_cut
    return body - bore
