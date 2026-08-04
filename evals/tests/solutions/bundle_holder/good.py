"""The reference holder: a U-channel on a back plate, the screw above the cradle."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    """bundle_diameter: cable bundle across, from measurements.toml"""
    plate, length = 2.4, 12.0
    channel = bundle_diameter + 0.4
    lip_h = plate + bundle_diameter / 2 + 2.0
    plate_h = bundle_diameter + 12.0
    width = plate + channel + plate

    back = Pos(plate / 2, 0, plate_h / 2) * Box(plate, length, plate_h)
    shelf = Pos(width / 2, 0, plate / 2) * Box(width, length, plate)
    lip = Pos(width - plate / 2, 0, lip_h / 2) * Box(plate, length, lip_h)
    hole_z = plate + bundle_diameter + 4.6
    hole = Pos(plate / 2, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, plate)
    return back + shelf + lip - hole
