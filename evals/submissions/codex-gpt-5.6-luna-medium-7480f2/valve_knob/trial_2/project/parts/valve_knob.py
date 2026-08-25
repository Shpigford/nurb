from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    knob_height: float = 16.0,
    grip_radius: float = 14.0,
    lobe_reach: float = 16.5,
    lobe_width: float = 4.0,
):
    """Replacement valve knob.

    shaft_diameter: measured round diameter of the valve stem
    shaft_across_flat: measured distance from the D flat to the opposite side
    knob_height: overall printed height of the knob
    grip_radius: radius between the six grip lobes
    lobe_reach: maximum radius at the grip lobes
    lobe_width: tangential width of each grip lobe
    """
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", param="shaft_across_flat")
    if lobe_reach <= grip_radius:
        reject("lobe_reach must exceed grip_radius to make the grip lobes", param="lobe_reach")

    # A 0.35 mm radial print-fit allowance lets the +0.3 mm test stem enter,
    # while the +1.0 mm stem is larger than this bore.
    bore_radius = shaft_diameter / 2.0 + 0.35
    bore_flat = shaft_across_flat / 2.0 + 0.35

    body = Cylinder(grip_radius, knob_height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Six short, fully grounded lobes provide a 14 mm minimum grip diameter
    # and a 16.5 mm maximum reach without spending material on a solid disk.
    lobe_center = (grip_radius + lobe_reach) / 2.0
    lobe_length = lobe_reach - grip_radius + 2.0
    for angle in range(0, 360, 60):
        lobe = Box(
            lobe_length,
            lobe_width,
            knob_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        lobe = Rot(0, 0, angle) * Pos(lobe_center, 0, 0) * lobe
        body = body + lobe

    # Clip the cylindrical negative space at +X to make the D flat face +X.
    # The bore is open from the printed top and extends through the knob.
    bore = Cylinder(bore_radius, knob_height + 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    clip = Pos(-bore_radius, -bore_radius, -0.1) * Box(
        bore_radius + bore_flat,
        2.0 * bore_radius,
        knob_height + 0.4,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    bore = bore & clip
    return body - bore
