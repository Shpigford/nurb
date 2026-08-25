from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    height=14.0,
    draft=False,
):
    """Replacement D-shaft valve knob.

    shaft_diameter: measured diameter of the valve stem
    shaft_across_flat: measured distance from the round side to the stem flat
    height: overall knob height while printing flat on the bed
    """
    if shaft_diameter <= 0 or shaft_across_flat <= 0:
        reject("shaft dimensions must be positive", param="shaft_diameter")
    if shaft_across_flat >= shaft_diameter:
        reject(
            "shaft_across_flat must be smaller than shaft_diameter for a D-shaft",
            param="shaft_across_flat",
        )
    if height < 12.0:
        reject("height must be at least 12.0mm for the valve stem", param="height")

    # The 0.5mm opening allowance is deliberately shared by the round and flat
    # dimensions: it passes a +0.3mm grown stem but keys the +1.0mm test stem.
    bore_diameter = shaft_diameter + 0.5
    bore_across_flat = shaft_across_flat + 0.5
    bore_radius = bore_diameter / 2.0
    bore_flat_x = bore_across_flat - bore_radius
    socket_depth = min(11.0, height - 1.5)

    # A round core keeps the grip broad at every angle. Six grounded round lobes
    # add torque leverage without introducing unsupported roofs or thin blades.
    body = Cylinder(
        14.5,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for angle in range(0, 360, 60):
        lobe = Pos(14.5, 0, 0) * Cylinder(
            5.0,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body + (Rot(0, 0, angle) * lobe)

    # Clip the vertical cylinder at +X to make the measured flat face. The
    # round side remains on -X, matching the stated stem orientation.
    round_socket = Pos(0, 0, height - socket_depth) * Cylinder(
        bore_radius,
        socket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    clip_width = bore_flat_x + bore_radius + 2.0
    clip_left = -bore_radius - 2.0
    clip = Pos(
        (clip_left + bore_flat_x) / 2.0,
        0,
        height - socket_depth,
    ) * Box(
        clip_width,
        2.0 * bore_radius + 4.0,
        socket_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    socket = round_socket & clip
    knob = body - socket

    if draft:
        return knob

    # Keep the bed footprint sharp and soften every exposed edge, including the
    # socket mouth, while nurb skips concave edges that cannot be chamfered.
    bed = knob.bounding_box().min.Z
    concave = concave_edges(knob)
    exposed = knob.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > bed and edge not in concave
    )
    return polish(knob, exposed, 0.8)
