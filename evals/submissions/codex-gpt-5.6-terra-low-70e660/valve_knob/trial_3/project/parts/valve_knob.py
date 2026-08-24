from nurb import *


@part
def valve_knob(
    shaft_diameter: float = measured("shaft_diameter"),
    shaft_across_flat: float = measured("shaft_across_flat"),
    knob_height: float = 14.0,
):
    """A four-lobed replacement knob for an 8 mm D-profile valve stem.

    shaft_diameter: diameter measured across the round part of the valve stem.
    shaft_across_flat: distance from the stem flat to its opposite round side.
    knob_height: printed height and engagement depth of the knob.
    """
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", param="shaft_across_flat")

    # Generous running clearance for FDM while retaining a positive-side D flat
    # that transmits torque after the knob is flipped onto the stem.
    bore_diameter = shaft_diameter + 0.8
    bore_radius = bore_diameter / 2
    bore_across_flat = shaft_across_flat + 0.8
    flat_x = bore_radius - bore_across_flat

    # A compact circular core keeps every wall thick; four radial pads provide
    # a wet-hand grip without taking the part beyond a modest print volume.
    body = Cylinder(14.0, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x, y in ((14.0, 0.0), (-14.0, 0.0), (0.0, 14.0), (0.0, -14.0)):
        body += Cylinder(5.0, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((x, y, 0))

    # D bore, vertical and open upward: circle clipped at the +X-facing flat.
    round_bore = Cylinder(bore_radius, knob_height + 0.2,
                          align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((0, 0, -0.1))
    keep_left_of_flat = Box(2 * bore_radius + 0.2, 2 * bore_radius + 0.2, knob_height + 0.4,
                            align=(Align.MAX, Align.CENTER, Align.MIN)).translate((-flat_x, 0, -0.1))
    d_bore = round_bore & keep_left_of_flat
    return body - d_bore
