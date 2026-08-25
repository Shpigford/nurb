from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
):
    """Replacement D-shaft valve knob, printed upright.

    shaft_diameter: measured round diameter of the valve stem
    shaft_across_flat: measured distance from the stem flat to its opposite tangent
    """
    # The fit stem is specified as +0.3mm on both measurements.  Add another
    # 0.5mm to the opening so the printed bore has real running clearance, but
    # keep the opening below the +1.0mm no-rattle stem.
    bore_diameter = shaft_diameter + 0.8
    bore_across_flat = shaft_across_flat + 0.8
    bore_radius = bore_diameter / 2.0
    bore_flat_x = bore_across_flat - bore_radius

    if bore_diameter >= shaft_diameter + 1.0:
        reject(
            "bore_diameter must stay below the +1.0mm anti-rattle stem; reduce the bore clearance",
            param="shaft_diameter",
        )
    if bore_across_flat >= shaft_across_flat + 1.0:
        reject(
            "bore_across_flat must stay below the +1.0mm anti-rattle stem; reduce the bore clearance",
            param="shaft_across_flat",
        )

    height = 16.0
    grip_radius = 15.0
    lobe_radius = 4.0
    lobe_centers = 14.0

    body = Cylinder(
        grip_radius,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for angle in range(0, 360, 60):
        a = radians(angle)
        body += Pos(lobe_centers * cos(a), lobe_centers * sin(a), 0) * Cylinder(
            lobe_radius,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    # A round bore clipped at +X makes the flat face point toward +X, matching
    # the stem orientation.  It opens at the top and stops well below the
    # 10mm engagement depth used by the fit test.
    bore_depth = 12.5
    round_bore = Pos(0, 0, height - bore_depth) * Cylinder(
        bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    clip = Pos(-20.0, 0, height - bore_depth) * Box(
        bore_flat_x + 20.0,
        40.0,
        bore_depth,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore & clip

    return body - d_bore
