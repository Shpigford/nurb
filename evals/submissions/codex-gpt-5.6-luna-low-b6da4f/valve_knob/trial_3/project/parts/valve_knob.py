from nurb import *


@part
def valve_knob(
    shaft_diameter=8.0,
    shaft_across_flat=6.5,
    knob_height=16.0,
    body_diameter=28.0,
    lobe_reach=18.0,
    bore_clearance=0.2,
):
    """Replacement D-shaft valve knob.

    shaft_diameter: measured round diameter of the valve stem
    shaft_across_flat: measured distance from the round side to the flat
    knob_height: total printed height of the knob
    body_diameter: narrow outside grip diameter at mid-height
    lobe_reach: outside reach of the four torque-grip lobes
    bore_clearance: radial clearance around the fitting stem
    """
    shaft_radius = shaft_diameter / 2.0
    # The fitting stem is grown by 0.3 mm in both measurements.  Add the
    # specified radial clearance to that test size, rather than guessing a
    # nominal printer offset.
    bore_radius = shaft_radius + 0.15 + bore_clearance
    bore_flat = shaft_across_flat / 2.0 + 0.15 + bore_clearance

    body = Cylinder(body_diameter / 2.0, knob_height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN))
    lobe_width = 6.0
    lobe_depth = lobe_reach - body_diameter / 2.0 + 1.0
    lobes = (
        Pos(0, body_diameter / 2.0 + lobe_depth / 2.0 - 0.5, 0)
        * Box(lobe_width, lobe_depth, knob_height,
              align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    lobes += (
        Pos(0, -(body_diameter / 2.0 + lobe_depth / 2.0 - 0.5), 0)
        * Box(lobe_width, lobe_depth, knob_height,
              align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    lobes += (
        Pos(body_diameter / 2.0 + lobe_depth / 2.0 - 0.5, 0, 0)
        * Box(lobe_depth, lobe_width, knob_height,
              align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    lobes += (
        Pos(-(body_diameter / 2.0 + lobe_depth / 2.0 - 0.5), 0, 0)
        * Box(lobe_depth, lobe_width, knob_height,
              align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    outside = body + lobes

    # D-shaped vertical socket, with the flat facing +X.  The clipping box
    # removes the +X cap of the circular bore at the measured flat location.
    bore_round = Cylinder(bore_radius, 12.5,
                           align=(Align.CENTER, Align.CENTER, Align.MIN))
    bore_clip = Pos(bore_flat - 50.0, 0, 2.0) * Box(
        100.0, 100.0, 12.5,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    bore = bore_round & bore_clip
    result = outside - bore

    # Keep the bed perimeter square and leave all fit-critical socket edges
    # untouched; the broad exterior lobes already have print-safe corners.
    return result
