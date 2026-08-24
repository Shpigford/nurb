from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=18.0,
    grip_radius=14.0,
    lobe_reach=18.0,
    fit_clearance=0.45,
    draft=False,
):
    """Three-lobed replacement valve knob, printed bore-up.

    shaft_diameter: measured diameter across the round side of the D-shaft
    shaft_across_flat: measured distance from the flat to the opposite round side
    knob_height: overall printed height
    grip_radius: radius of the central hand grip
    lobe_reach: distance from center to the end of each turning lobe
    fit_clearance: radial clearance around the measured stem
    """
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", "shaft_across_flat")

    # A 28 mm round core supplies the minimum wet-hand grip; two low-profile
    # lobes provide positive leverage without a bulky solid disk.
    body = Cylinder(grip_radius, knob_height)
    lobe_radius = 4.0
    lobe_offset = lobe_reach - lobe_radius
    body = body + Cylinder(lobe_radius, knob_height).translate((lobe_offset, 0, 0))
    body = body + Cylinder(lobe_radius, knob_height).translate((-lobe_offset, 0, 0))

    # The printed socket opens at +Z. Across-flat is measured from the flat
    # (at +X) to the opposite round side, so it controls the D-flat directly.
    bore_radius = shaft_diameter / 2.0 + fit_clearance
    bore_across_flat = shaft_across_flat + 2.0 * fit_clearance
    flat_x = -bore_radius + bore_across_flat
    bore_depth = 12.0
    bore_center_z = knob_height / 2.0 - bore_depth / 2.0
    round_bore = Cylinder(bore_radius, bore_depth).translate((0, 0, bore_center_z))
    # Primitives are center-aligned. This limiting box starts at the round
    # side (-X radius) and stops on the required +X-facing flat.
    d_limit = Box(bore_radius + flat_x, 2.0 * bore_radius, bore_depth).translate(
        ((flat_x - bore_radius) / 2.0, 0, bore_center_z)
    )
    d_bore = round_bore & d_limit
    return body - d_bore
