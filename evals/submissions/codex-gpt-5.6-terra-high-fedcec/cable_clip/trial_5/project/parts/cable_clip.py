from nurb import *


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A screw-down, open-top clip for one cable bundle.

    bundle_diameter: measured diameter of the cable bundle held by the channel.
    draft: skips no geometry; retained for the standard part interface.
    """
    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than zero", param="bundle_diameter")

    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter
    wall_thickness = 2.4
    base_thickness = 3.0
    part_length = 12.0
    tab_length = 10.0
    mounting_hole_diameter = 4.2

    # The base includes the mounting tab. The two walls rise directly from it,
    # leaving a square-cornered, full-length channel above the flat base face.
    overall_width = tab_length + 2.0 * wall_thickness + channel_width
    base = Box(overall_width, part_length, base_thickness)

    tab_right = -overall_width / 2.0 + tab_length
    left_wall = Box(wall_thickness, part_length, channel_depth).translate(
        (tab_right + wall_thickness / 2.0, 0.0, base_thickness / 2.0 + channel_depth / 2.0)
    )
    right_wall = Box(wall_thickness, part_length, channel_depth).translate(
        (tab_right + wall_thickness + channel_width + wall_thickness / 2.0,
         0.0,
         base_thickness / 2.0 + channel_depth / 2.0)
    )

    body = base.fuse(left_wall, right_wall)
    mounting_hole = Cylinder(
        mounting_hole_diameter / 2.0,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).translate((-overall_width / 2.0 + tab_length / 2.0, 0.0, 0.0))
    return body.cut(mounting_hole)
