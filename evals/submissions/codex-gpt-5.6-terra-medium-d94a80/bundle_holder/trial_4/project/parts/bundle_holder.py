from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """A compact, wall-mounted through-channel cable-bundle holder.

    bundle_diameter: measured diameter of the cable bundle passing through the holder
    """
    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be positive", param="bundle_diameter")

    # The channel is deliberately 0.4 mm over the measured bundle diameter.
    channel_diameter = bundle_diameter + 0.4
    channel_radius = channel_diameter / 2.0
    length = 10.0
    back_thickness = 3.0
    shelf_top = 8.1
    channel_center_x = back_thickness + channel_radius + 0.1
    channel_center_z = shelf_top + channel_radius + 0.2

    # A tall, thin back gives a generous flat wall interface while keeping the M4
    # head well clear of the cable channel.
    back = Box(back_thickness, length, 26.5,
               align=(Align.MIN, Align.MIN, Align.MIN))

    # The 45-degree underside lets the cable floor grow out of the back without a
    # floating shelf.  It is extruded continuously along the cable run.
    shelf_landing = channel_center_x - 1.3
    slope_start_z = shelf_top - (shelf_landing - back_thickness)
    rail_inner = channel_center_x + channel_radius + 0.6
    shelf_profile = Polygon((back_thickness, 0), (back_thickness, slope_start_z),
                            (shelf_landing, shelf_top), (rail_inner, shelf_top),
                            (rail_inner, 0))
    shelf = extrude(shelf_profile, amount=length).rotate(Axis.X, 90)

    # A front rail keeps the bundle from walking away from the wall; its opening is
    # still a full-length tunnel, so a bundle can be threaded through from either end.
    rail_outer = rail_inner + 2.4
    rail_top = channel_center_z + channel_radius / 2.0
    rail_profile = Polygon((rail_inner - 0.2, shelf_top), (rail_inner, shelf_top),
                           (rail_outer, shelf_top + 2.4), (rail_outer, rail_top),
                           (rail_inner, rail_top))
    rail = extrude(rail_profile, amount=length).rotate(Axis.X, 90).move(Pos(0, length, 0))
    body = back.fuse(shelf).fuse(rail)

    # M4 clearance bore from the wall, followed by an 8.8 mm pan-head/driver relief.
    # The 3 mm back is the solid seat between the two diameters.
    screw_z = 20.8
    shank = Cylinder(2.2, back_thickness).rotate(Axis.Y, 90).move(Pos(0, length / 2, screw_z))
    head_relief = Cylinder(4.4, 20.0).rotate(Axis.Y, 90).move(Pos(back_thickness, length / 2, screw_z))
    return body.cut(shank.fuse(head_relief))
