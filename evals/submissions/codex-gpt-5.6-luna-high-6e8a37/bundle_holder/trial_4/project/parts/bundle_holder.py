from nurb import *


@part
def bundle_holder(bundle_diameter: float = 8.0, length: float = 16.0):
    """
    A flat-printing wall holder for a horizontal cable bundle.

    bundle_diameter: diameter of the cable bundle that passes through the holder
    length: length of the holder along the bundle
    """
    clearance = 0.4
    back_thickness = 2.4
    shelf_thickness = 1.6
    retainer_thickness = 2.0
    retainer_gap = 0.8
    screw_diameter = 4.4

    bundle_radius = bundle_diameter / 2.0
    bundle_center_z = shelf_thickness + clearance + bundle_radius
    bundle_top = bundle_center_z + bundle_radius

    # The tall rear spine is the wall-contacting face and carries the screw.
    # The shelf and front rail form a supported, open cable tunnel.
    retainer_x = back_thickness + bundle_diameter + retainer_gap
    retainer_height = bundle_top + clearance - shelf_thickness
    screw_z = bundle_top + 4.8
    total_height = screw_z + screw_diameter / 2.0
    outer_depth = retainer_x + retainer_thickness

    back = Pos(back_thickness / 2.0, length / 2.0, total_height / 2.0) * Box(
        back_thickness, length, total_height
    )
    shelf = Pos(outer_depth / 2.0, length / 2.0, shelf_thickness / 2.0) * Box(
        outer_depth, length, shelf_thickness
    )
    front_retainer = Pos(
        retainer_x + retainer_thickness / 2.0,
        length / 2.0,
        shelf_thickness + retainer_height / 2.0,
    ) * Box(retainer_thickness, length, retainer_height)

    body = back + shelf + front_retainer

    # The screw enters from the wall side (+X), with a 2.4 mm thick bearing
    # section before its head seats against the front of the rear spine.
    screw_bore = Pos(
        back_thickness / 2.0,
        length / 2.0,
        screw_z,
    ) * Box(back_thickness, screw_diameter, screw_diameter)
    body = body - screw_bore

    return body
