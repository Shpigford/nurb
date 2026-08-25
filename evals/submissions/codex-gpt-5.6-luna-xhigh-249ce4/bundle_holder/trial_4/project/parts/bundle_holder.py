from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """One-screw wall holder for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle
    """
    clearance = 0.4
    length = 18.0

    # The bundle has a 0.4mm total fit allowance and runs in +Y.
    bundle_radius = (bundle_diameter + clearance) / 2.0
    # Keep the floor below the installed M4 head's lowest z (6.0 - 4.2),
    # while still leaving a 0.4mm fit gap beneath the bundle.
    floor_thickness = 1.6
    bundle_center_z = floor_thickness + clearance + bundle_radius

    # A low spine supplies more than 100mm2 of flat wall contact.  The taller,
    # thicker boss is local to the screw, and stays behind the bundle in +X.
    spine_depth = 2.6
    spine_height = 6.0
    boss_depth = 4.2
    boss_width = 10.4
    boss_height = 12.0
    boss_y = (length - boss_width) / 2.0
    screw_z = 6.0

    spine = Box(spine_depth, length, spine_height,
                align=(Align.MIN, Align.MIN, Align.MIN))
    boss = Pos(0, boss_y, 0) * Box(
        boss_depth, boss_width, boss_height,
        align=(Align.MIN, Align.MIN, Align.MIN)
    )

    # The floor blocks a one-millimetre downward move.  The front rail blocks
    # the same bundle from moving one millimetre away from the wall.
    bundle_center_x = boss_depth + clearance + bundle_radius
    rail_inner_x = bundle_center_x + bundle_radius + clearance
    rail_thickness = 1.6
    rail_height = 6.0
    floor = Pos(spine_depth, 0, 0) * Box(
        rail_inner_x + rail_thickness - spine_depth,
        length,
        floor_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN)
    )
    # Leave the screw's 8.4mm head/driver path open through the middle.  The
    # two end sections still provide 8.8mm of +X retention over 48.9% of Y.
    rail_end_length = 4.4
    rail_front = Pos(rail_inner_x, 0, floor_thickness) * Box(
        rail_thickness,
        rail_end_length,
        rail_height,
        align=(Align.MIN, Align.MIN, Align.MIN)
    )
    rail_back = Pos(rail_inner_x, length - rail_end_length, floor_thickness) * Box(
        rail_thickness,
        rail_end_length,
        rail_height,
        align=(Align.MIN, Align.MIN, Align.MIN)
    )
    rail = rail_front + rail_back

    body = spine + boss + floor + rail

    # M4 medium clearance through the back, with an 8.4mm head/driver pocket
    # beginning 2.5mm into the part.  Both cuts run along +X.
    screw_clearance = 4.4
    screw_head_clearance = 8.4
    seat_x = 2.5
    bore = Pos(0, length / 2.0, screw_z) * Rot(0, 90, 0) * Cylinder(
        screw_clearance / 2.0,
        boss_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    head_pocket = Pos(seat_x, length / 2.0, screw_z) * Rot(0, 90, 0) * Cylinder(
        screw_head_clearance / 2.0,
        boss_depth - seat_x,
        align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    body = body - bore - head_pocket

    if draft:
        return body

    # The retaining rail meets the floor in a tight structural junction. Keep
    # those load-bearing and fit-critical edges sharp so the polish pass cannot
    # create unsupported cosmetic strips or sub-mm slivers.
    return body
