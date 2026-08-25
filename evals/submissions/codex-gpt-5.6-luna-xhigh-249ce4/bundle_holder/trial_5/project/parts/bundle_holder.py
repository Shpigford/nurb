from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall holder for a horizontal cable bundle.

    bundle_diameter: measured diameter of the bundle being retained
    """
    if bundle_diameter < 5.0:
        reject("bundle_diameter must be at least 5.0mm for this holder; use a smaller clip", param="bundle_diameter")

    length = 18.0
    floor_thickness = 2.4
    bundle_clearance = 0.4
    retainer_thickness = 2.4
    floor_depth = 13.8
    retainer_x = 11.4
    retainer_height = floor_thickness + bundle_clearance + bundle_diameter + 0.2

    # The central back boss is deliberately narrower than the cable run. The wall
    # closes the back of the run while the boss leaves the measured bundle in free air.
    back_thickness = 2.4
    back_width = 10.0
    back_y = (length - back_width) / 2.0
    screw_y = length / 2.0
    screw_z = retainer_height + 4.8
    back_height = screw_z + 5.0
    screw_bore = 4.4

    floor = Pos(0, 0, 0) * Box(
        floor_depth,
        length,
        floor_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    retainer = Pos(retainer_x, 0, 0) * Box(
        retainer_thickness,
        length,
        retainer_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    back = Pos(0, back_y, 0) * Box(
        back_thickness,
        back_width,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    # The M4 bore is normal to the wall. Its front rim is the pan-head seat;
    # everything forward of that rim is left clear for the 8.4mm head and driver.
    bore = Pos(0, screw_y, screw_z) * Rot(0, 90, 0) * Cylinder(
        screw_bore / 2.0,
        back_thickness + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = floor + retainer + back - bore

    if draft:
        return body

    # The cradle junction and the small rail corners are functional geometry;
    # leaving them square avoids polish slivers and keeps the printability report
    # honest about the retained section.
    return body
