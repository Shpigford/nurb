from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter: float = 8.0,
    shaft_across_flat: float = 6.5,
    knob_height: float = 16.0,
    grip_diameter: float = 32.0,
    lobe_reach: float = 18.5,
    bore_clearance: float = 0.7,
    floor_thickness: float = 3.0,
    draft: bool = False,
):
    """Replacement D-shaft valve knob.

    shaft_diameter: diameter of the valve stem's round portion
    shaft_across_flat: distance from the stem flat to its opposite round side
    knob_height: overall height of the knob above the bed
    grip_diameter: diameter across the narrow waist of the grip
    lobe_reach: radius at the six hand-grip lobes
    bore_clearance: extra fit clearance added to both measured shaft dimensions
    floor_thickness: material left below the blind shaft socket
    """
    if shaft_across_flat >= shaft_diameter:
        reject("shaft_across_flat must be smaller than shaft_diameter", param="shaft_across_flat")
    if floor_thickness >= knob_height - 2.0:
        reject("floor_thickness must leave at least 2mm of socket depth", param="floor_thickness")

    # A six-lobed outline gives a broad, wet-hand-friendly grip without wasting
    # the material of a much larger solid cylinder.
    inner_r = grip_diameter / 2.0
    points = []
    for i in range(12):
        angle = i * 30.0
        radius = lobe_reach if i % 2 == 0 else inner_r
        points.append((radius * cos(radians(angle)), radius * sin(radians(angle))))
    body = extrude(Polygon(*points), amount=knob_height)

    # Build a D-shaped blind socket.  The flat is on +X, matching the stem;
    # the circle and the flat are both derived from the exposed parameters.
    bore_radius = shaft_diameter / 2.0 + bore_clearance / 2.0
    bore_flat_x = shaft_across_flat / 2.0 + bore_clearance / 2.0
    socket_depth = knob_height - floor_thickness
    round_bore = Pos(0, 0, floor_thickness) * Cylinder(
        bore_radius, socket_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    flat_clip = Pos((-bore_radius + bore_flat_x) / 2.0, 0, floor_thickness) * Box(
        bore_radius + bore_flat_x,
        2.0 * bore_radius,
        socket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    socket = round_bore & flat_clip
    result = body - socket

    # The socket is fit-critical and its concave rim must stay sharp. The
    # scalloped perimeter is already faceted for a reliable, support-free
    # print, so leave the functional solid un-dressed.
    return result
