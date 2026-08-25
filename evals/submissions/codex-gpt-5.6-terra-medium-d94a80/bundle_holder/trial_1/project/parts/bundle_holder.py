from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Low-profile, wall-mounted channel for one horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle being retained
    """
    if bundle_diameter <= 0.0:
        reject("bundle_diameter must be greater than zero", param="bundle_diameter")

    # The three inside faces make an 0.4 mm oversize rectangular berth. The
    # wall closes the fourth direction, while the floor and front rail retain
    # the bundle downward and away from the wall.
    fit_clearance = 0.4
    opening = bundle_diameter + fit_clearance
    back_thickness = 3.0
    holder_length = 12.5
    floor_thickness = 2.4
    rail_thickness = 2.4

    rail_x = back_thickness + opening
    rail_height = opening

    # The screw is above the cable. Its 4.4 mm clearance bore is through the
    # full 3 mm wall, leaving a solid 3 mm seat before the head is in free air.
    back_height = floor_thickness + opening + 8.2
    screw_z = back_height - 3.5
    screw_y = holder_length / 2.0

    back = Pos(back_thickness / 2.0, holder_length / 2.0, back_height / 2.0) * Box(back_thickness, holder_length, back_height)
    # A small overlap with the rail makes the three members one fused solid
    # without reducing the 8.4 mm clear cable space above the floor.
    floor = Pos(back_thickness + (opening + 0.1) / 2.0, holder_length / 2.0, floor_thickness / 2.0) * Box(opening + 0.1, holder_length, floor_thickness)
    # The rail runs to the bed instead of starting on a floating shelf, so it
    # prints as a simple vertical wall without support.
    rail = Pos(rail_x + rail_thickness / 2.0, holder_length / 2.0, (rail_height + floor_thickness) / 2.0) * Box(rail_thickness, holder_length, rail_height + floor_thickness)
    body = back.fuse(floor).fuse(rail)

    # Axis is X: the opening is on the wall-facing back and a standard M4
    # shank has 0.2 mm radial print clearance.
    bore = Pos(0, screw_y, screw_z) * Cylinder(2.2, back_thickness + 0.1, rotation=(0, 90, 0))
    return body.cut(bore)
