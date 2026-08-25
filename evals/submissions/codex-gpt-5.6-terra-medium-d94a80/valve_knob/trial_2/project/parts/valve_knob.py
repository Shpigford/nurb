from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    knob_radius=14.5,
    knob_height=16.0,
    socket_depth=12.0,
    fit_clearance=0.35,
    draft=False,
):
    """A replacement hand knob for an 8 mm D-shaft valve.

    shaft_diameter: diameter across the round portion of the valve stem
    shaft_across_flat: distance from the stem flat to its opposite round side
    knob_radius: radius of the round hand grip
    knob_height: printed height of the knob
    socket_depth: how far the stem enters from the top
    fit_clearance: radial and flat-side allowance around the measured stem
    """
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be less than shaft_diameter", param="shaft_across_flat")
    if socket_depth < 10.5 or socket_depth >= knob_height:
        reject("socket_depth must be at least 10.5 mm and leave a bottom floor", param="socket_depth")

    grip = Cylinder(
        knob_radius,
        knob_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    lobe = Pos(14.0, 0, 0) * Cylinder(
        4.0,
        knob_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = grip.fuse(lobe)

    # The D socket is defined from both stem dimensions. Its flat faces +X.
    bore_radius = shaft_diameter / 2 + fit_clearance
    bore_flat_x = shaft_across_flat - shaft_diameter / 2 + fit_clearance
    round_bore = Pos(0, 0, knob_height - socket_depth) * Cylinder(
        bore_radius,
        socket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_cut = Pos(bore_flat_x, 0, knob_height - socket_depth) * Box(
        bore_radius * 2,
        bore_radius * 2,
        socket_depth,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_socket = round_bore.cut(flat_cut)
    result = body.cut(d_socket)

    return result
