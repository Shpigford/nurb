from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall-mounted channel for a horizontal cable bundle.

    bundle_diameter: measured width of the cable bundle held by the channel
    """
    if bundle_diameter < 4.0:
        reject(
            "bundle_diameter must be at least 4.0mm for this holder geometry",
            param="bundle_diameter",
        )

    length = 12.0
    back_thickness = 2.5
    base_thickness = 3.0
    channel_clearance = 0.6
    channel_width = bundle_diameter + channel_clearance
    front_wall_thickness = 2.4

    channel_left = back_thickness
    channel_right = channel_left + channel_width
    front_x = channel_right
    outer_x = front_x + front_wall_thickness

    bundle_center_z = base_thickness + bundle_diameter / 2 + 0.3
    front_height = bundle_center_z + bundle_diameter / 2 + 0.8

    screw_z = front_height + 7.0
    back_height = screw_z + 5.0
    screw_y = length / 2
    screw_seat_x = back_thickness

    back = Box(
        back_thickness,
        length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    base = Box(
        outer_x,
        length,
        base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    front = Pos(front_x, 0, 0) * Box(
        front_wall_thickness,
        length,
        front_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    holder = back + base + front

    shank_bore = (
        Cylinder(2.2, back_thickness + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        .rotate(Axis.Y, 90)
        .translate((-0.5, screw_y, screw_z))
    )
    head_clearance = (
        Cylinder(4.2, back_thickness + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        .rotate(Axis.Y, 90)
        .translate((screw_seat_x, screw_y, screw_z))
    )
    holder = holder - shank_bore - head_clearance

    return holder
