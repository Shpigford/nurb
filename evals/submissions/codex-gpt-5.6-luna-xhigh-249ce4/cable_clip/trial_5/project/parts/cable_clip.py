from nurb import *


@part
def cable_clip(bundle_diameter: float = measured("bundle_diameter"), draft=False):
    """Screw-down clip for a cable bundle.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    channel_depth = bundle_diameter
    base_thickness = 3.0
    length = 12.0
    outer_width = channel_width + 2.0 * wall_thickness
    tab_length = 10.0
    hole_diameter = 4.2

    body = Pos(tab_length, 0, 0) * Box(
        outer_width,
        length,
        base_thickness + channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    mounting_tab = Box(
        tab_length,
        length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    solid = body + mounting_tab

    channel_void = Pos(
        tab_length + wall_thickness,
        0,
        base_thickness,
    ) * Box(
        channel_width,
        length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    screw_hole = Pos(tab_length / 2.0, length / 2.0, -0.1) * Cylinder(
        hole_diameter / 2.0,
        base_thickness + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    solid = solid - channel_void - screw_hole

    return solid
