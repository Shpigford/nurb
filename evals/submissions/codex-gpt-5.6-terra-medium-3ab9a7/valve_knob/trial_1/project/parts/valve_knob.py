from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=14.0,
    bore_clearance=0.45,
    draft=False,
):
    """A three-lobed replacement knob for an 8 mm D-shaft.

    shaft_diameter: diameter across the stem's round side.
    shaft_across_flat: distance from the stem flat to its opposite round side.
    knob_height: printed height of the knob.
    bore_clearance: radial and flat-side clearance around the measured stem.
    """
    if shaft_diameter <= 0.0 or shaft_across_flat <= 0.0:
        reject("shaft dimensions must be positive", param="shaft_diameter")
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", param="shaft_across_flat")
    if knob_height < 12.0:
        reject("knob_height must be at least 12.0 mm", param="knob_height")
    if bore_clearance < 0.3:
        reject("bore_clearance must be at least 0.3 mm for the driven stem", param="bore_clearance")

    # A 28 mm-diameter core guarantees a substantial grip in every direction;
    # the three rounded lobes give wet hands positive purchase without excess mass.
    core_radius = 14.5
    lobe_radius = 6.5
    lobe_center = 11.0
    body = Cylinder(core_radius, knob_height)
    for angle in (0.0, 120.0, 240.0):
        lobe = Cylinder(lobe_radius, knob_height).translate((lobe_center, 0.0, 0.0))
        body = body.fuse(lobe.rotate(Axis.Z, angle))

    # D-bore prints open upward. The stem flat faces +X: cutting the positive-X
    # segment from a circular bore leaves the flat at this computed coordinate.
    bore_radius = shaft_diameter / 2.0 + bore_clearance
    bore_across_flat = shaft_across_flat + 2.0 * bore_clearance
    flat_x = bore_across_flat - bore_radius
    bore_depth = knob_height - 1.0  # 1 mm closed cap at the printed bottom
    round_bore = Cylinder(bore_radius, bore_depth).translate((0.0, 0.0, 1.0))
    flat_cut = Box(
        bore_radius + 2.0,
        2.0 * bore_radius + 2.0,
        bore_depth + 1.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).translate((flat_x, 0.0, -knob_height / 2.0 + 1.0))
    d_bore = round_bore.fuse(flat_cut)
    return body.cut(d_bore)
