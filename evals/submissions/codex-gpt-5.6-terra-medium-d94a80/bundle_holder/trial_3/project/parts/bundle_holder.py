from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """Low-profile wall clip for one horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle held by the clip
    """
    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than zero", param="bundle_diameter")

    # The holder is deliberately an open, printable channel: the cable can thread in
    # from either end, while the floor and outer rail retain it in service.
    clearance = 0.4
    back_thickness = 2.6
    length = 12.0
    cable_radius = bundle_diameter / 2.0
    # The rail overlaps the floor by 0.2 mm for a reliable boolean fuse, leaving
    # an actual channel width of bundle_diameter + 0.8 mm.
    channel_width = bundle_diameter + 1.0
    floor_height = cable_radius - 0.4
    cable_center_z = floor_height + clearance + cable_radius
    lip_thickness = 1.2
    lip_height = cable_radius + 2.0
    screw_center_z = cable_center_z + cable_radius + 4.2
    back_height = screw_center_z + 4.5

    back = Box(back_thickness, length, back_height,
               align=(Align.MIN, Align.MIN, Align.MIN))
    floor = Pos(back_thickness, 0, 0) * Box(channel_width, length, floor_height,
                                               align=(Align.MIN, Align.MIN, Align.MIN))
    # Overlap the floor slightly so the three printed members fuse into one solid.
    lip = Pos(back_thickness + channel_width - 0.2, 0, floor_height) * Box(
        lip_thickness, length, lip_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body = back + floor + lip

    # A plain M4 clearance bore enters at the wall.  Everything in front of the
    # 2.4 mm back plate is intentionally open around the pan-head and driver.
    bore = Pos(0, length / 2.0, screw_center_z) * Rot(0, 90, 0) * Cylinder(
        2.2, back_thickness + 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return body - bore
