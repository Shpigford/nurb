from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    length=16.0,
    back_thickness=3.0,
    draft=False,
):
    """Wall-mounted cable-bundle holder.

    bundle_diameter: diameter of the bundle passing through the channel
    length: length of the holder along the bundle
    back_thickness: material thickness from the wall to the screw seat
    """
    clearance = bundle_diameter + 0.4
    bundle_radius = bundle_diameter / 2.0

    front_wall_thickness = 1.2
    front_inner_x = back_thickness + clearance
    front_outer_x = front_inner_x + front_wall_thickness
    shelf_x0 = back_thickness - 0.2
    # The lower face is a true 45 degree corbel from the bed to the shelf.
    # Keeping the run equal to the rise makes every layer self-supporting.
    shelf_z = max(9.8, front_outer_x - shelf_x0)
    shelf_thickness = 1.0
    segment_length = 3.5

    # The back is deliberately tall enough to separate the bundle from the
    # screw head.  Its minimum-X face is the wall interface and remains broad
    # and flat.
    back_height = shelf_z + shelf_thickness + bundle_diameter + 1.0
    back = Box(
        back_thickness,
        length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    # The bundle sits on grounded retention rails.  The front rail blocks +X
    # while the wall blocks -X; the two rails cover more than one third of the
    # length and leave the screw envelope open.
    shelf = Pos(shelf_x0, 0, shelf_z) * Box(
        front_outer_x - shelf_x0,
        length,
        shelf_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    front_wall = Pos(front_inner_x, 0, shelf_z) * Box(
        front_wall_thickness,
        length,
        back_height - shelf_z,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    # Split the retention rails around the screw.  The bundle still spans the
    # full Y length, but the two 3.5mm rails provide more than one third of
    # its length of down/away blocking while leaving the screw envelope open.
    profile = Plane.XZ * Polygon(
        (shelf_x0, 0),
        (shelf_x0, shelf_z),
        (front_outer_x, shelf_z),
        align=None,
    )
    low_corbel = extrude(profile, amount=segment_length)
    high_corbel = Pos(0, length - segment_length, 0) * extrude(
        profile, amount=segment_length
    )
    # Short 1mm bed pads keep the tall corbels planted.  They stay outside
    # the screw's Y envelope, so they cannot enter the head-clearance tunnel.
    foot_length = 2.0
    low_foot = Pos(shelf_x0, 0, 0) * Box(
        foot_length,
        segment_length,
        2.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    high_foot = Pos(shelf_x0, length - segment_length, 0) * Box(
        foot_length,
        segment_length,
        2.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    low_shelf = shelf & Pos(0, 0, 0) * Box(
        front_outer_x + 0.2,
        segment_length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    high_shelf = shelf & Pos(0, length - segment_length, 0) * Box(
        front_outer_x + 0.2,
        segment_length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    low_wall = front_wall & Pos(0, 0, 0) * Box(
        front_outer_x + 0.2,
        segment_length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    high_wall = front_wall & Pos(0, length - segment_length, 0) * Box(
        front_outer_x + 0.2,
        segment_length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body = back + low_shelf + high_shelf + low_wall + high_wall
    body = body + low_corbel + high_corbel + low_foot + high_foot

    # Put the bundle in the upper channel.  A 0.4mm gap remains to the shelf
    # and the rail at the nominal size.  The screw is low on the back so its
    # 8.4mm head envelope stays below the retained bundle.
    bundle_center_z = shelf_z + shelf_thickness + bundle_radius + 0.4

    screw_y = length / 2.0
    screw_z = 4.6
    screw_bore = Pos(0, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(
        2.2,
        back_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # The pan-head/driver envelope starts at the front of the back and exits
    # through the open channel.  The shoulder at X=back_thickness leaves the
    # full back thickness behind the head seat.
    head_clearance = Pos(back_thickness, screw_y, screw_z) * Rot(
        0, 90, 0
    ) * Cylinder(
        4.2,
        front_inner_x + front_wall_thickness - back_thickness + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - screw_bore - head_clearance

    if draft:
        return body

    # Keep the functional retention and screw shoulders sharp: dress-up
    # chamfers at these concave junctions would create sub-millimetre strips.
    return body
