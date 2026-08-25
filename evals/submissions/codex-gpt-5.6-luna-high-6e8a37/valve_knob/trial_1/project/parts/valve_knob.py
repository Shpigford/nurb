import math

from nurb import *


_SHAFT_DIAMETER = float(measured("shaft_diameter"))
_SHAFT_ACROSS_FLAT = float(measured("shaft_across_flat"))


@part
def valve_knob(
    shaft_diameter=_SHAFT_DIAMETER,
    shaft_across_flat=_SHAFT_ACROSS_FLAT,
    knob_height=14.0,
    bore_depth=11.0,
    draft=False,
):
    """Replacement valve knob.

    shaft_diameter: measured round diameter of the valve stem
    shaft_across_flat: measured distance from the stem flat to its far side
    knob_height: overall height of the knob while it prints
    bore_depth: depth of the D socket from the top face
    """
    if shaft_diameter <= 0 or shaft_across_flat <= 0:
        reject("shaft dimensions must be positive", param="shaft_diameter")
    if knob_height < 12.0:
        reject("knob_height must be at least 12.0mm for the stem engagement", param="knob_height")
    if bore_depth < 10.5 or bore_depth >= knob_height - 1.5:
        reject("bore_depth must leave at least 1.5mm of material below the socket and reach 10mm", param="bore_depth")

    # The clearance is deliberately derived from both measured D-shaft dimensions.
    # The flat location is the round radius subtracted from the across-flat size.
    bore_diameter = shaft_diameter + 0.8
    bore_across_flat = shaft_across_flat + 0.8
    bore_radius = bore_diameter / 2.0
    bore_flat_x = bore_across_flat - bore_radius
    if bore_flat_x <= 0 or bore_flat_x >= bore_radius:
        reject("shaft dimensions do not describe a usable D-shaft", param="shaft_across_flat")

    # A central drum keeps the minimum grip width above 28mm. Six overlapping
    # round lobes make the maximum reach substantially wider than that waist.
    core_radius = 15.5
    lobe_radius = 3.5
    lobe_centres = 15.0
    body = Cylinder(
        core_radius,
        knob_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for index in range(6):
        angle = math.radians(index * 60.0)
        body = body + Pos(
            lobe_centres * math.cos(angle),
            lobe_centres * math.sin(angle),
            0,
        ) * Cylinder(
            lobe_radius,
            knob_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    # Intersect the round socket with a half-space ending at the +X-facing flat.
    # The socket opens at the top and stops 3mm above the bed.
    socket_z = knob_height - bore_depth
    round_socket = Pos(0, 0, socket_z) * Cylinder(
        bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_clip = Pos(-2.0 * bore_radius, 0, socket_z) * Box(
        2.0 * bore_radius + bore_flat_x,
        4.0 * bore_radius,
        bore_depth,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_socket = round_socket & flat_clip
    body = body - d_socket

    if draft:
        return body

    # Dress only the exposed upper and lower outline; the socket wall stays
    # dimensionally honest for the fit and torque tests.
    exposed = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z >= knob_height - 0.01
    )
    return polish(body, exposed, 0.8)
