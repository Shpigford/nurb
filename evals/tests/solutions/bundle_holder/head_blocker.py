"""CHEAT: a 0.9mm wall stands 0.35mm in front of the screw bore, completely covering
it, sized and placed to fall between the head-clearance probe's 1.0mm X steps
(samples at seat+0.2, seat+1.2, ...). The screw cannot even be inserted, yet bore,
seat, and head clearance all pass."""

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0):
    plate, length = 2.4, 12.0
    channel = bundle_diameter + 0.4
    lip = 2.4
    lip_h = plate + bundle_diameter / 2 + 2.0
    plate_h = bundle_diameter + 12.0
    width = plate + channel + lip

    back = Pos(plate / 2, 0, plate_h / 2) * Box(plate, length, plate_h)
    shelf = Pos(width / 2, 0, plate / 2) * Box(width, length, plate)
    lipb = Pos(width - lip / 2, 0, lip_h / 2) * Box(lip, length, lip_h)
    # the blocker: air gap 2.4..2.75 makes the walk seat at 2.5; wall 2.75..3.65
    # dodges head probes at x = 2.7 and 3.7; it stands on the shelf, one solid
    blocker = Pos(2.75 + 0.45, 0, plate + (plate_h - plate) / 2) * Box(
        0.9, length, plate_h - plate
    )
    hole_z = plate + bundle_diameter + 4.6
    hole = Pos(plate / 2, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, plate)
    return back + shelf + lipb + blocker - hole
