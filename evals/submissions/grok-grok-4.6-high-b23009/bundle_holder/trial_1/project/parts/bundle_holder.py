from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """Wall clip for a cable bundle that runs along the wall.

    bundle_diameter: width of the taped bundle the clip holds
    """
    if bundle_diameter < 3.0:
        reject(
            "bundle_diameter is under 3mm; raise it so the clip can print around the bundle",
            param="bundle_diameter",
        )

    plate = 2.4
    length = 12.0
    channel = bundle_diameter + 0.4
    lip_h = plate + bundle_diameter / 2 + 2.0
    plate_h = bundle_diameter + 12.0
    width = plate + channel + plate
    hole_z = plate + bundle_diameter + 4.6

    back = Pos(plate / 2, 0, plate_h / 2) * Box(plate, length, plate_h)
    shelf = Pos(width / 2, 0, plate / 2) * Box(width, length, plate)
    lip = Pos(width - plate / 2, 0, lip_h / 2) * Box(plate, length, lip_h)
    hole = Pos(plate / 2, 0, hole_z) * Rot(0, 90, 0) * Cylinder(2.2, plate)
    return back + shelf + lip - hole
