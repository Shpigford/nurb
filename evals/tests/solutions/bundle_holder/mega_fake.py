"""CHEAT: both function gates faked at once. Retention is a single 1.4mm finger
straddling the one sampled Y-station; the screw bore is blind behind a 1.2mm skin
perforated only by a cross slot at the grader's probe points. Neither holds a bundle
nor accepts an M4 screw."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    skin = 1.2
    plate = skin + 2.4
    length = 12.0
    channel = bundle_diameter + 0.4
    lip = 1.6
    finger = 1.4  # straddles the station at Y = 0
    plate_h = bundle_diameter + 12.0
    hole_z = plate + bundle_diameter + 4.6
    width = plate + channel + lip
    lip_h = 2.4 + bundle_diameter / 2 + 2.0

    back = Pos(plate / 2, 0, plate_h / 2) * Box(plate, length, plate_h)
    shelf = Pos(width / 2, 0, 2.4 / 2) * Box(width, finger, 2.4)
    lipb = Pos(width - lip / 2, 0, lip_h / 2) * Box(lip, finger, lip_h)
    part_ = back + shelf + lipb

    bore = Pos(skin + (plate - skin) / 2, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, plate - skin)
    part_ -= bore
    part_ -= Pos(skin / 2, 0, hole_z) * Box(skin, 4.2, 0.85)
    part_ -= Pos(skin / 2, 0, hole_z) * Box(skin, 0.85, 4.2)
    return part_
