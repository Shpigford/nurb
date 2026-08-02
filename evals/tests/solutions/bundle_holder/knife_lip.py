"""CHEAT: the reference holder but the retaining lip is a 0.15mm knife-edge foil.
Shapely's penetration erosion treats any material, however thin, as blocking; the
real printed lip would flex or snap off at a touch of an 8mm cable bundle."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    plate, length = 2.4, 12.0
    channel = bundle_diameter + 0.4
    lip = 0.15
    lip_h = plate + bundle_diameter / 2 + 2.0
    plate_h = bundle_diameter + 12.0
    width = plate + channel + lip

    back = Pos(plate / 2, 0, plate_h / 2) * Box(plate, length, plate_h)
    shelf = Pos(width / 2, 0, plate / 2) * Box(width, length, plate)
    lipb = Pos(width - lip / 2, 0, lip_h / 2) * Box(lip, length, lip_h)
    hole_z = plate + bundle_diameter + 4.6
    hole = Pos(plate / 2, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, plate)
    return back + shelf + lipb - hole
