"""CHEAT: retention satisfied by a single 1.4mm-long finger straddling the one
Y-station at part mid-length. 10.6mm of the 12mm part is bare plate; the bundle is
'retained' by a fingernail of plastic and falls out with any wiggle."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    plate, length = 2.4, 12.0
    channel = bundle_diameter + 0.4
    lip = 1.6
    finger = 1.4  # straddles the station at Y = 0
    plate_h = bundle_diameter + 12.0
    hole_z = plate + bundle_diameter + 4.6
    width = plate + channel + lip
    lip_h = plate + bundle_diameter / 2 + 2.0

    back = Pos(plate / 2, 0, plate_h / 2) * Box(plate, length, plate_h)
    shelf = Pos(width / 2, 0, plate / 2) * Box(width, finger, plate)
    lipb = Pos(width - lip / 2, 0, lip_h / 2) * Box(lip, finger, lip_h)
    hole = Pos(plate / 2, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, plate)
    return back + shelf + lipb - hole
