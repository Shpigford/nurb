from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall holder for a horizontal cable bundle.

    bundle_diameter: outside diameter of the cable bundle
    """
    if bundle_diameter < 4.0:
        reject("bundle_diameter must be at least 4.0mm for the retained channel", param="bundle_diameter")

    length = 12.0
    back_thickness = 3.0
    floor_thickness = 2.6
    front_wall_thickness = 3.0

    # The bundle has 0.4mm of air below it and 0.4mm at the back.
    bundle_radius = bundle_diameter / 2.0
    bundle_center_x = back_thickness + 0.4 + bundle_radius
    bundle_center_z = floor_thickness + 0.4 + bundle_radius
    front_wall_x = back_thickness + bundle_diameter + 1.0
    front_wall_height = bundle_center_z + bundle_radius + 1.0

    # Keep the head passage above the retained bundle as its diameter changes.
    screw_z = bundle_center_z + bundle_radius + 6.0
    back_height = screw_z + 6.0

    floor = Box(
        front_wall_x + front_wall_thickness,
        length,
        floor_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    back = Box(
        back_thickness,
        length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    front = Pos(front_wall_x, 0, 0) * Box(
        front_wall_thickness,
        length,
        front_wall_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    holder = floor + back + front

    # M4 medium clearance through the 3mm back, then an 8.4mm driver/head
    # passage from the seat all the way through the open channel.
    screw_y = length / 2.0
    shank_bore = Pos(-0.1, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(
        2.2, back_thickness + 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    head_passage = Pos(back_thickness, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(
        4.2,
        front_wall_x + front_wall_thickness - back_thickness + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    holder = holder - shank_bore - head_passage

    if draft:
        return holder

    return holder
