from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), length=14.0,
                  back_thickness=2.6, floor_thickness=2.4,
                  retention_wall_thickness=2.4, draft=False):
    """Wall holder for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle
    length: length of the holder along the bundle
    back_thickness: material between the wall and the bundle
    floor_thickness: thickness under the bundle
    retention_wall_thickness: thickness of the front retaining wall
    """
    clearance = 0.4
    bundle_clear = bundle_diameter + clearance
    channel_width = bundle_clear
    channel_height = bundle_clear

    # The bundle sits 0.4mm above the floor and is centered in the clear channel.
    # The screw is deliberately above it so the pan head cannot occupy the cable bay.
    floor_z = floor_thickness
    bundle_center_z = floor_z + clearance + bundle_diameter / 2
    screw_center_z = bundle_center_z + bundle_clear / 2 + 4.2 + 0.6
    back_height = screw_center_z + 4.2 + 0.4

    min_align = (Align.MIN, Align.MIN, Align.MIN)
    back = Box(back_thickness, length, back_height, align=min_align)
    floor = Pos(back_thickness, 0, 0) * Box(
        channel_width, length, floor_thickness, align=min_align
    )
    front = Pos(back_thickness + channel_width, 0, 0) * Box(
        retention_wall_thickness, length,
        bundle_center_z + bundle_diameter / 2 + 0.6, align=min_align
    )
    body = back + floor + front

    # M4 medium-clearance bore, horizontal through the back plate.  Its front face
    # is the screw seat; the rest of the channel is intentionally empty there.
    screw_bore = Pos(0, length / 2, screw_center_z) * Rot(0, 90, 0) * Cylinder(
        radius=2.2, height=back_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    body = body - screw_bore

    if draft:
        return body

    # The channel walls are intentionally left square: their 2.4mm sections are
    # functional retention and the screw seat needs a clean, full-thickness face.
    return body
