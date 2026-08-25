from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter")):
    """Wall-mounted open cradle for a horizontal cable bundle.

    bundle_diameter: measured width across the cable bundle
    """
    clearance = 0.4
    part_length = 12.0
    wall_thickness = 3.0
    floor_thickness = 2.6
    front_thickness = 2.6

    channel_width = bundle_diameter + clearance
    outer_depth = wall_thickness + channel_width + front_thickness

    # The front lip rises past the cable centre, so it blocks motion away
    # from the wall while leaving the top open for support-free printing.
    front_height = floor_thickness + 0.8 * bundle_diameter

    bundle_top = floor_thickness + 0.2 + bundle_diameter
    screw_head_radius = 4.2
    screw_center_z = bundle_top + 0.8 + screw_head_radius
    back_height = screw_center_z + screw_head_radius + 0.4

    anchored = (Align.MIN, Align.MIN, Align.MIN)
    floor = Box(outer_depth, part_length, floor_thickness, align=anchored)
    back = Box(wall_thickness, part_length, back_height, align=anchored)
    front = Pos(wall_thickness + channel_width, 0, 0) * Box(
        front_thickness, part_length, front_height, align=anchored
    )

    holder = floor + back + front

    # A 4.4 mm M4 through-bore opens at the wall face.  Its seat is the
    # front of the 3 mm back plate; the pan head and driver remain entirely
    # in free space above the retained cable path.
    screw_bore = Pos(-0.1, part_length / 2, screw_center_z) * Cylinder(
        2.2,
        wall_thickness + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).rotate(Axis.Y, 90)

    return holder - screw_bore
