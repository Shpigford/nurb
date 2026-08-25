from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """Screw-down cable clip with a square, open-top channel.

    bundle_diameter: measured cable bundle diameter; sets the channel width and depth
    """
    channel_depth = bundle_diameter
    channel_width = bundle_diameter + 0.4
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    hole_diameter = 4.2

    channel_width_overall = channel_width + 2.0 * wall_thickness
    channel_height = base_thickness + channel_depth

    # Box and Cylinder are center-placed.  Put the tab from X=-5..5 and the
    # channel from X=5..18.2, with the complete bottom on Z=0.
    tab = Pos(0, 0, base_thickness / 2.0) * Box(
        tab_length, part_length, base_thickness
    )
    channel_center_x = tab_length / 2.0 + channel_width_overall / 2.0
    channel = Pos(channel_center_x, 0, channel_height / 2.0) * Box(
        channel_width_overall, part_length, channel_height
    )
    body = tab.fuse(channel)

    # Removing only the space above the 3 mm floor leaves one continuous flat floor.
    channel_void = Pos(
        channel_center_x,
        0,
        base_thickness + channel_depth / 2.0,
    ) * Box(channel_width, part_length, channel_depth)
    body = body.cut(channel_void)

    # The hole is vertical and fully contained in the flat mounting tab.
    screw_hole = Pos(0, 0, base_thickness / 2.0) * Cylinder(
        hole_diameter / 2.0, base_thickness
    )
    return body.cut(screw_hole)
