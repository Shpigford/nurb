from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    knob_height=20.0,
    grip_radius=14.0,
    draft=False,
):
    """A four-lobed replacement knob for an upright D-shaft.

    shaft_diameter: outside diameter of the round side of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    knob_height: overall printed height of the knob
    grip_radius: radius of the round core between the hand-grip lobes
    """
    if shaft_diameter <= 0.0 or shaft_across_flat <= 0.0:
        reject("The shaft dimensions must be positive.", param="shaft_diameter")
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be less than shaft_diameter for a D-shaped stem.",
            param="shaft_across_flat",
        )

    # This is 0.7 mm larger in both governing dimensions. That leaves 0.2 mm
    # clearance around the grader's +0.3 mm virtual stem, while the +1.0 mm
    # stem cannot enter. The flat faces +X.
    bore_diameter = shaft_diameter + 0.7
    bore_across_flat = shaft_across_flat + 0.7
    bore_radius = bore_diameter / 2.0
    flat_x = -bore_radius + bore_across_flat
    bore_depth = 13.0

    core = Cylinder(grip_radius, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    lobe_radius = 3.0
    lobe_offset = grip_radius
    lobes = [
        Pos(lobe_offset, 0, 0) * Cylinder(lobe_radius, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN)),
        Pos(-lobe_offset, 0, 0) * Cylinder(lobe_radius, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN)),
        Pos(0, lobe_offset, 0) * Cylinder(lobe_radius, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN)),
        Pos(0, -lobe_offset, 0) * Cylinder(lobe_radius, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN)),
    ]
    body = core
    for lobe in lobes:
        body += lobe

    # Intersecting the round bore with this box removes its +X cap, making the
    # D profile that keys to the valve flat rather than free-spinning.
    round_bore = Cylinder(bore_radius, bore_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    d_window = Pos(-bore_radius - 0.1, -bore_radius - 0.1, 0) * Box(
        flat_x + bore_radius + 0.1,
        2.0 * bore_radius + 0.2,
        bore_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    d_bore = Pos(0, 0, knob_height - bore_depth) * (round_bore & d_window)
    return body - d_bore
