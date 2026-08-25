from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall-mounted cable bundle cradle.

    bundle_diameter: measured diameter of the cable bundle the cradle retains
    """
    length = 11.0
    clearance = 0.4
    inner_diameter = bundle_diameter + clearance
    radial_clearance = (inner_diameter - bundle_diameter) / 2.0
    bundle_radius = bundle_diameter / 2.0

    # The back is the minimum-X wall face.  The shelf and front lip are both
    # grounded on the bed, making the open J-shaped cradle support-free.
    back_thickness = 4.0
    shelf_end = None
    shelf_thickness = 3.0
    lip_start = None
    back_height = 22.0

    bundle_center_x = back_thickness + radial_clearance + bundle_radius
    bundle_center_z = shelf_thickness + radial_clearance + bundle_radius
    # Leave 0.8 mm of free space before the lip: a 1 mm outward move then
    # enters the lip while the nominal cylinder remains entirely clear.
    lip_start = bundle_center_x + bundle_radius + 0.8
    lip_width = 3.0
    shelf_end = lip_start + lip_width
    lip_height = bundle_center_z + 1.0

    back = Box(
        back_thickness,
        length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    shelf = Box(
        shelf_end,
        length,
        shelf_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    front_lip = Pos(lip_start, 0, 0) * Box(
        shelf_end - lip_start,
        length,
        lip_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body = back + shelf + front_lip

    # The screw runs along +X.  Keep 2.4 mm of back material before the
    # counterbore seat; the wider pocket is open toward +X for the pan head
    # and driver.  The exact 4.4 mm bore is the requested M4 clearance.
    screw_y = length / 2.0
    screw_z = bundle_center_z + bundle_radius + 2.7
    bore = Pos(0, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(
        2.2,
        2.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    head_pocket = Pos(2.4, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(
        4.5,
        shelf_end - 2.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - bore - head_pocket

    if draft:
        return body
    # Keep the retention stops and the screw seat dimensionally exact.  A
    # blanket chamfer here creates concave cosmetic strips at both grounded
    # junctions and sub-millimetre corner slivers, so the functional profile
    # intentionally remains sharp.
    return body
