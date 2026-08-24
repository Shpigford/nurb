from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    height: float = 16.0,
    grip_radius: float = 14.5,
    lobe_radius: float = 3.0,
    bore_clearance: float = 0.4,
):
    """Replacement knob for a D-shaft valve.

    shaft_diameter: measured round diameter of the valve stem
    shaft_across_flat: measured distance from the flat to the opposite round side
    height: overall knob height above the print bed
    grip_radius: radius of the central grip body
    lobe_radius: radius of each wet-hand grip lobe
    bore_clearance: diametral allowance for a sliding printed fit
    """
    # The six overlapping lobes make the narrow grip 29 mm across while
    # extending the widest reach to 17.5 mm for positive torque.
    body = Cylinder(grip_radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for angle in range(0, 360, 60):
        body += Rot(Z=angle) * Pos(grip_radius, 0, 0) * Cylinder(
            lobe_radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )

    # A D bore is a round bore clipped at the flat.  The stem enters from the
    # top and stops in a 5 mm floor, leaving a 11 mm engaged pocket.
    bore_diameter = shaft_diameter + bore_clearance
    bore_flat = shaft_across_flat + bore_clearance
    flat_x = bore_flat - bore_diameter / 2.0
    round_bore = Pos(0, 0, 5) * Cylinder(
        bore_diameter / 2.0, height - 5.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_limit = Pos(-20, -20, 5) * Box(
        20 + flat_x, 40, height - 4.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    d_bore = round_bore & flat_limit
    return body - d_bore
