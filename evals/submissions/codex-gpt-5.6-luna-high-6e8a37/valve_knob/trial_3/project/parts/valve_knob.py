"""Replacement knob for the measured D-shaft valve stem."""

from nurb import *


@part
def valve_knob(
    shaft_diameter=measured("shaft_diameter"),
    shaft_across_flat=measured("shaft_across_flat"),
    height=18.0,
    grip_radius=14.2,
    lobe_radius=2.5,
    lobe_center_radius=15.5,
    bore_depth=13.0,
    draft=False,
):
    """A support-free, six-lobe valve knob with a keyed D-shaft bore.

    shaft_diameter: diameter of the round part of the valve stem
    shaft_across_flat: distance from the stem's +X flat to its opposite tangent
    height: overall knob height above the print bed
    grip_radius: radius of the plain central grip at mid-height
    lobe_radius: radius of each rounded finger lobe
    lobe_center_radius: distance from the axis to each lobe centre
    bore_depth: depth of the keyed bore down from the top face
    """
    if height < 14.0:
        reject("height must be at least 14mm for the valve stem engagement", param="height")
    if bore_depth >= height - 2.0:
        reject("bore_depth must leave at least 2mm of material at the bottom", param="bore_depth")
    if grip_radius < 14.0:
        reject("grip_radius must leave at least a 28mm grip diameter", param="grip_radius")

    # The fit stem is +0.3mm in both measured dimensions.  The extra margin
    # here leaves useful printed clearance while keeping the +1.0mm test stem
    # larger than the bore in both directions.
    bore_diameter = shaft_diameter + 0.8
    bore_across_flat = shaft_across_flat + 0.7
    bore_radius = bore_diameter / 2.0
    bore_flat_x = bore_across_flat - bore_radius
    bore_bottom = height - bore_depth

    body = Cylinder(
        grip_radius,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Rounded lobes overlap the central cylinder, making one solid while
    # extending the reach well beyond the 28mm minimum grip diameter.
    for angle in range(0, 360, 60):
        lobe = Pos(lobe_center_radius, 0, 0) * Cylinder(
            lobe_radius,
            height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body + (Rot(0, 0, angle) * lobe)

    # A D-shaped cutter: the circular bore is clipped by a flat facing +X.
    # Its straight wall is keyed, so a rotated D-stem cannot pass through.
    round_bore = Pos(0, 0, bore_bottom) * Cylinder(
        bore_radius,
        bore_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flat_cutter = Pos(bore_flat_x, 0, bore_bottom) * Box(
        10.0,
        30.0,
        bore_depth,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    d_bore = round_bore - flat_cutter
    return body - d_bore
