from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """A support-free, single-screw cable-bundle holder.

    bundle_diameter: measured diameter of the cable bundle held in the channel.
    """
    # The channel is deliberately a little larger than the measured bundle. The
    # bottom shelf stops downward motion and the short front rail stops pull-out.
    clearance = 0.5
    channel_radius = bundle_diameter / 2.0 + clearance
    length = 10.0
    back_thickness = 3.0
    shelf_top = 5.75
    channel_center_x = back_thickness + channel_radius + clearance
    channel_center_z = shelf_top + channel_radius + clearance
    # This is 0.5 mm clear of the actual bundle, but overlaps it after the
    # specified 1 mm pull-out movement.
    rail_inner_x = channel_center_x + bundle_diameter / 2.0 + clearance
    rail_thickness = 3.0
    rail_top = channel_center_z - 1.0
    # The fastener sits above the channel, so its driver clearance is completely
    # outside the retaining rail and cannot form an unsupported pocket ceiling.
    back_height = max(24.0, channel_center_z + channel_radius + 2.0)

    # All three masses meet the bed, so the holder prints in its installed
    # orientation: X is wall-to-room and Z is vertical.
    origin = (Align.MIN, Align.MIN, Align.MIN)
    back = Box(back_thickness, length, back_height, align=origin)
    shelf = Box(rail_inner_x, length, shelf_top, align=origin)
    rail = Box(rail_thickness, length, rail_top, align=origin).translate(
        (rail_inner_x, 0, 0)
    )
    body = back.fuse(shelf).fuse(rail)

    # M4 medium-clearance bore. The 8.8 mm relief starts after the 3 mm back
    # wall, leaving a shank guide before the pan head seats and a clear driver
    # path all the way through the front rail.
    screw_y = length / 2.0
    screw_z = 20.0
    shank = Cylinder(2.2, back_thickness + 0.2, rotation=(0, 90, 0)).translate(
        (back_thickness + 0.1, screw_y, screw_z)
    )
    head_relief = Cylinder(
        4.4, rail_inner_x + rail_thickness - back_thickness + 0.2,
        rotation=(0, 90, 0)
    ).translate((rail_inner_x + rail_thickness + 0.1, screw_y, screw_z))
    return body.cut(shank.fuse(head_relief))
