from nurb import *


@part
def bundle_holder(bundle_diameter: float = measured("bundle_diameter"), draft=False):
    """Wall holder for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle
    """
    clearance = 0.4
    tunnel_diameter = bundle_diameter + clearance
    tunnel_height = tunnel_diameter + 0.4

    length = 12.0
    back_thickness = 4.0
    back_height = 21.0
    rail_thickness = 1.2
    # The cable seat stays centered on z=0 while the mounting spine rises above it.
    tunnel_bottom = -tunnel_height / 2.0
    tunnel_top = tunnel_height / 2.0

    back = Pos(0, 0, 2.5) * Box(back_thickness, length, back_height)
    rail_span = 10.4
    rail_center_x = back_thickness / 2.0 + rail_span / 2.0
    # Extend the lower rail to the bed.  This is the print-support spine and
    # also makes the forward footprint stable without a suspended underside.
    lower_rail = Pos(rail_center_x, 0, (-8.0 + tunnel_bottom) / 2.0) * Box(
        rail_span, length, tunnel_bottom + 8.0
    )
    upper_rail = Pos(rail_center_x, 0, tunnel_top + rail_thickness / 2.0) * Box(
        rail_span, length, rail_thickness
    )
    front_rail = Pos(11.8, 0, (tunnel_bottom + tunnel_top) / 2.0) * Box(
        1.2, length, tunnel_height + 2.0 * rail_thickness
    )
    holder = back + lower_rail + upper_rail + front_rail

    # M4 medium-clearance bore, opening on the wall face.  The enlarged
    # forward pocket clears the complete pan-head/driver envelope.
    screw_y = 0.0
    screw_z = 7.5
    bore = Pos(0.0, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(2.2, 4.0)
    head_clearance = Pos(6.9, screw_y, screw_z) * Box(12.2, 8.4, 8.4)
    holder = holder - bore - head_clearance
    return holder
