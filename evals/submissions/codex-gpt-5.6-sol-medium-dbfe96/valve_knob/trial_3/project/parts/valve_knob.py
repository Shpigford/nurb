from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
):
    """A low-profile four-paddle replacement valve knob.

    shaft_diameter: diameter of the valve stem's round portion
    shaft_across_flat: distance from the stem's flat to its opposite round side
    """
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )

    height = 16.0
    hub_radius = 14.0
    paddle_reach = 19.0
    paddle_width = 10.0

    hub = Cylinder(
        hub_radius,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    x_paddles = Box(
        paddle_reach * 2.0,
        paddle_width,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    y_paddles = Box(
        paddle_width,
        paddle_reach * 2.0,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = hub + x_paddles + y_paddles

    # Printed bores close slightly, so give the measured D-shaft 0.6 mm total
    # clearance on both controlling dimensions.  Keep the flat toward +X.
    bore_allowance = 0.6
    bore_diameter = shaft_diameter + bore_allowance
    bore_across_flat = shaft_across_flat + bore_allowance
    bore_radius = bore_diameter / 2.0
    bore_flat_x = bore_across_flat - bore_radius
    bore_depth = 12.0

    round_bore = Pos(0, 0, height - bore_depth) * Cylinder(
        bore_radius,
        bore_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_limiter = Pos(
        (bore_flat_x - bore_radius) / 2.0,
        0,
        height - bore_depth,
    ) * Box(
        bore_flat_x + bore_radius,
        bore_diameter,
        bore_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore & flat_limiter

    return body - d_bore
