from math import cos, radians, sin

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    height=16.0,
    grip_radius=14.5,
    lobe_radius=4.0,
    lobe_center_radius=14.4,
    draft=False,
):
    """Replacement knob for the measured D-shaped valve stem.

    shaft_diameter: round diameter of the valve stem
    shaft_across_flat: distance from the stem's flat to its round side
    height: overall knob height
    grip_radius: radius of the central hand grip
    lobe_radius: radius of each rounded finger lobe
    lobe_center_radius: distance from the centerline to each lobe center
    """
    bore_clearance = 0.6
    bore_radius = (shaft_diameter + bore_clearance) / 2.0
    bore_across_flat = shaft_across_flat + bore_clearance
    bore_flat_x = -bore_radius + bore_across_flat
    bore_depth = 13.0

    grip = Cylinder(
        grip_radius,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    if not draft:
        grip_top = grip.edges().filter_by(
            lambda edge: edge.bounding_box().min.Z > height - 0.01
        )
        grip = polish(grip, grip_top, 1.0)

    for index in range(6):
        angle = radians(index * 60.0)
        lobe = Pos(
            lobe_center_radius * cos(angle),
            lobe_center_radius * sin(angle),
            0,
        ) * Cylinder(
            lobe_radius,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        if not draft:
            lobe_top = lobe.edges().filter_by(
                lambda edge: edge.bounding_box().min.Z > height - 0.01
            )
            lobe = polish(lobe, lobe_top, 1.0)
        grip = grip + lobe

    bore_cylinder = Pos(0, 0, height - bore_depth) * Cylinder(
        bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bore_half_space = Pos(bore_flat_x - 100.0, 0, height - bore_depth) * Box(
        100.0,
        200.0,
        bore_depth,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_bore = bore_cylinder & bore_half_space

    return grip - d_bore
