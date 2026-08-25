from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), length=12.0, draft=False):
    """A one-screw wall clip for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle held in the channel
    length: how far the clip runs along the cable and wall
    """
    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be positive", param="bundle_diameter")
    if length < 10.0:
        reject("length must be at least 10mm for a stable cable run", param="length")

    wall_thickness = 3.0
    shelf_thickness = 3.0
    rail_thickness = 2.4
    fit_clearance = 0.4
    bundle_radius = bundle_diameter / 2.0

    # The cable has 0.4mm clearance to the wall plate, shelf, and retaining rail.
    bundle_center_x = wall_thickness + fit_clearance + bundle_radius
    bundle_center_z = shelf_thickness + fit_clearance + bundle_radius
    rail_x = bundle_center_x + bundle_radius + fit_clearance
    rail_top = bundle_center_z + 1.0

    # The M4 head is above the cable and clears the rail by more than its 8.4mm diameter.
    screw_z = bundle_center_z + bundle_radius + 3.0
    back_height = screw_z + 5.0

    back = Box(wall_thickness, length, back_height,
               align=(Align.MIN, Align.CENTER, Align.MIN))
    shelf = Pos(wall_thickness, 0, 0) * Box(
        rail_x + rail_thickness - wall_thickness, length, shelf_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    rail = Pos(rail_x, 0, shelf_thickness) * Box(
        rail_thickness, length, rail_top - shelf_thickness,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )

    # An M4 clearance bore runs from the wall to the front face of the 3mm-thick plate.
    # At that face the 8.4mm pan head and driver immediately have open space in +X.
    bore = Pos(0, 0, screw_z) * Rot(0, 90, 0) * Cylinder(2.2, wall_thickness)
    return (back + shelf + rail) - bore
