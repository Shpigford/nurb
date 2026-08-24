from nurb import *


@part
def valve_knob(
    shaft_diameter: float = measured("shaft_diameter"),
    shaft_across_flat: float = measured("shaft_across_flat"),
    height: float = 18.0,
    grip_diameter: float = 28.0,
    lobe_reach: float = 3.0,
    wall: float = 3.0,
):
    """Replacement valve knob.

    shaft_diameter: diameter of the valve stem
    shaft_across_flat: distance from the stem flat to its opposite round side
    height: overall knob height
    grip_diameter: diameter across the central grip
    lobe_reach: extra radial reach of the six wet-hand grip lobes
    wall: radial material around the D bore
    """
    # Give the fit a real 0.30 mm radial allowance.  The flat is kept, so the
    # bore keys the knob and transmits torque instead of acting like a round hole.
    bore_radius = shaft_diameter / 2.0 + 0.30
    bore_flat_x = shaft_across_flat - shaft_diameter / 2.0 + 0.30
    bore = Cylinder(bore_radius, height + 2.0)
    bore = bore & (
        Pos(-bore_radius - 1.0, -bore_radius - 1.0, -1.0)
        * Box(bore_radius + bore_flat_x + 1.0, 2.0 * bore_radius + 2.0, height + 2.0)
    )

    body = Cylinder(grip_diameter / 2.0, height)
    # Six overlapping round lobes make a forgiving, printable grip while
    # keeping the narrowest section at the central 28 mm diameter.
    lobe_radius = lobe_reach
    # Centres sit 1 mm inside the central rim so every lobe is one connected solid.
    lobe_centres = grip_diameter / 2.0 - 1.0
    for angle in range(0, 360, 60):
        body = body + (
            Rot(0, 0, angle)
            * Pos(lobe_centres, 0, 0)
            * Cylinder(lobe_radius, height)
        )

    result = body.cut(bore)
    if height < 12.0:
        reject("height must leave at least 12 mm of knob height", "height")
    if wall < 1.0:
        reject("wall must be at least 1 mm", "wall")
    return result
