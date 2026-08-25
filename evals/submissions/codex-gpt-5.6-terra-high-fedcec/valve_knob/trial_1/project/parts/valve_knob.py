"""A compact three-lobed replacement handle for an 8 mm D-shaft valve."""

from math import cos, pi, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    knob_height: float = 18.0,
    core_radius: float = 14.0,
    lobe_radius: float = 4.6,
    draft: bool = False,
):
    """A grippy, support-free valve knob.

    shaft_diameter: diameter across the round side of the valve stem
    shaft_across_flat: distance from the stem's flat to its opposite round side
    knob_height: overall height of the knob as printed
    core_radius: radius of the round central gripping body
    lobe_radius: extra radius of each of the three finger lobes
    """
    # Three shallow lobes make a wet-hand grip without the material cost of a
    # large round wheel.  They overlap the core, leaving a single solid.
    body = Cylinder(core_radius, knob_height)
    lobe_center = core_radius - 0.5 * lobe_radius
    for angle in (0.0, 2.0 * pi / 3.0, 4.0 * pi / 3.0):
        body = body + Cylinder(lobe_radius, knob_height).translate(
            (lobe_center * cos(angle), lobe_center * sin(angle), 0)
        )

    # The bore is deliberately a D, not a round hole.  Clearance is applied
    # to both recorded stem dimensions: it clears a 0.3 mm grown stem but a
    # 1.0 mm grown one cannot rattle in it.  The flat faces +X as printed.
    bore_diameter = shaft_diameter + 0.7
    bore_across_flat = shaft_across_flat + 0.7
    bore_radius = bore_diameter / 2.0
    flat_x = bore_across_flat - bore_radius
    bore_depth = 12.0
    # Primitives are centred at the origin.  Set the bore's centre so it opens
    # at the top face and reaches a full 12 mm down into the printed part.
    bore_z = knob_height / 2.0 - bore_depth / 2.0
    round_bore = Cylinder(bore_radius, bore_depth).translate((0, 0, bore_z))
    flat_limit = Box(bore_radius + flat_x + 1.0, 2.0 * bore_radius + 2.0, bore_depth + 0.2).translate(
        ((flat_x - bore_radius - 1.0) / 2.0, 0, bore_z)
    )
    d_bore = round_bore & flat_limit
    result = body - d_bore

    # Keep the printed base square and the D-bore sharp: both are functional
    # interfaces, and a cosmetic edge treatment there would reduce bed contact
    # or soften the torque-transmitting flat.
    return result
