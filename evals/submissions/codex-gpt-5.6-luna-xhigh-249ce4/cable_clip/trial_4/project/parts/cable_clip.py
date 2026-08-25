from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down cable clip for a cable bundle running along Y.

    bundle_diameter: diameter of the cable bundle; the channel opening grows with it
    draft: retained as the standard nurb build toggle; this exact-fit clip stays square
    """
    channel_clearance = 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    mounting_hole_diameter = 4.2

    channel_inner_width = bundle_diameter + channel_clearance
    channel_outer_width = channel_inner_width + 2.0 * wall_thickness
    channel_height = base_thickness + bundle_diameter

    # The channel is centered on the Y length and open at both ends.  The
    # rectangular cut leaves a single, uninterrupted, square-edged floor.
    channel = Box(
        channel_outer_width,
        part_length,
        channel_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel_opening = Pos(wall_thickness, 0, base_thickness) * Box(
        channel_inner_width,
        part_length,
        bundle_diameter,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel = channel - channel_opening

    # The tab is flush with the bed and meets the outside of the left wall.
    tab = Pos(-tab_length, 0, 0) * Box(
        tab_length,
        part_length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    mounting_hole = Pos(
        -tab_length / 2.0,
        part_length / 2.0,
        0,
    ) * Cylinder(
        mounting_hole_diameter / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    body = (channel + tab) - mounting_hole
    # Keep every exterior and channel edge square: the specified inner floor and
    # walls are fit-critical, and no cosmetic material is needed for this clip.
    return body
