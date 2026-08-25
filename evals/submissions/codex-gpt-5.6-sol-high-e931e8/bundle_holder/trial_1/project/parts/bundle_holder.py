from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A wall-mounted channel that retains a horizontal cable bundle.

    bundle_diameter: measured width across the cable bundle
    """
    if bundle_diameter < 2.0:
        reject(
            "bundle_diameter must be at least 2.0 mm for a printable holder",
            param="bundle_diameter",
        )

    length = 12.0
    clearance = 0.4
    channel_width = bundle_diameter + clearance

    back_thickness = 3.0
    floor_thickness = 2.4
    front_wall_thickness = 2.4

    screw_hole_width = 4.4
    screw_head_width = 8.4
    screw_head_radius = screw_head_width / 2
    screw_clearance_above_channel = 0.4

    channel_top = floor_thickness + channel_width
    screw_height = channel_top + screw_head_radius + screw_clearance_above_channel
    back_height = screw_height + screw_head_radius + 0.6
    outer_depth = back_thickness + channel_width + front_wall_thickness

    back = Box(
        back_thickness,
        length,
        back_height,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    floor = Box(
        outer_depth,
        length,
        floor_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    front_wall = Pos(back_thickness + channel_width, 0, 0) * Box(
        front_wall_thickness,
        length,
        channel_top,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )

    screw_bore = (
        Pos(0, 0, screw_height)
        * Rot(0, 90, 0)
        * Cylinder(
            screw_hole_width / 2,
            back_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    return (back + floor + front_wall) - screw_bore
