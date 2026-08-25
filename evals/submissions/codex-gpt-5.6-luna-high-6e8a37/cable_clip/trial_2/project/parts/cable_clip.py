from nurb import *


_DEFAULT_BUNDLE_DIAMETER = measured("bundle_diameter")


@part
def cable_clip(bundle_diameter=_DEFAULT_BUNDLE_DIAMETER, draft=False):
    """Screw-down clip for a cable bundle running along Y.

    bundle_diameter: diameter of the cable bundle held by the channel
    """
    channel_inner_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    channel_outer_width = channel_inner_width + 2.0 * wall_thickness
    base_thickness = 3.0
    channel_depth = bundle_diameter
    length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2

    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than 0 mm", param="bundle_diameter")

    # The tab and channel floor are both grounded, so the whole part prints
    # in its functional orientation without supports.
    base = Box(
        channel_outer_width,
        length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    tab = Pos(channel_outer_width, 0, 0) * Box(
        tab_length,
        length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    left_wall = Pos(0, 0, base_thickness) * Box(
        wall_thickness,
        length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    right_wall = Pos(channel_outer_width - wall_thickness, 0, base_thickness) * Box(
        wall_thickness,
        length,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    body = base + tab + left_wall + right_wall

    mounting_hole = Pos(
        channel_outer_width + tab_length / 2.0,
        length / 2.0,
        0,
    ) * Cylinder(
        hole_diameter / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - mounting_hole
