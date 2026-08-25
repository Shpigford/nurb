from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=16.0,
    draft=False,
):
    """Three-lobed replacement knob for an 8 mm D-shaft.

    shaft_diameter: measured diameter across the round portion of the valve stem
    shaft_across_flat: distance from the D-flat to the opposite round side of the stem
    knob_height: overall printed height of the knob
    """
    # The bore is deliberately 0.4 mm larger than the measured stem in both
    # controlling dimensions. The flat is the +X-facing wall of the bore.
    bore_diameter = shaft_diameter + 0.8
    bore_across_flat = shaft_across_flat + 0.8
    bore_radius = bore_diameter / 2.0
    flat_x = bore_across_flat - bore_radius

    # A compact round core with three broad lobes gives a sure wet-hand grip
    # without a large, material-heavy disk.
    core = Cylinder(14.5, knob_height)
    lobe_radius = 6.0
    lobe_offset = 13.5
    body = core
    for x, y in (
        (lobe_offset, 0.0),
        (-lobe_offset / 2.0, lobe_offset * 0.8660254),
        (-lobe_offset / 2.0, -lobe_offset * 0.8660254),
    ):
        body = body + Cylinder(lobe_radius, knob_height).translate((x, y, 0.0))

    # Print bore-up. Remove the +X circular cap from the cylindrical void to
    # leave a true D-shaped socket, then cut it 12 mm deep from the top.
    round_void = Cylinder(bore_radius, 12.0).translate(
        (0.0, 0.0, knob_height / 2.0 - 6.0)
    )
    cap_width = bore_radius - flat_x + 1.0
    cap = Box(cap_width, bore_diameter + 2.0, 14.0).translate(
        (flat_x + cap_width / 2.0, 0.0, knob_height / 2.0 - 6.0)
    )
    d_bore = round_void - cap
    return body - d_bore
