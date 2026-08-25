from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall-mounted cable-bundle holder.

    bundle_diameter: measured diameter of the cable bundle.
    """
    clearance = 0.4
    run = 15.0
    back_thickness = 3.0
    back_height = 22.0
    cradle_thickness = 2.4
    front_thickness = 1.6

    bundle_clear = bundle_diameter + 2.0 * clearance
    bundle_x = back_thickness + bundle_clear / 2.0
    bundle_bottom = cradle_thickness + clearance
    bundle_top = bundle_bottom + bundle_clear
    front_start = bundle_x + bundle_clear / 2.0 + 0.2
    front_end = front_start + front_thickness

    # All primitives are explicitly MIN-aligned so the back is the x=0 wall face
    # and the part sits on z=0 without a hidden translation.
    back = Box(
        back_thickness,
        run,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    cradle = Pos(back_thickness - 0.2, 0, 0) * Box(
        front_end - (back_thickness - 0.2),
        run,
        cradle_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    rail = Pos(front_start, 1.5, cradle_thickness - 0.2) * Box(
        front_thickness,
        run - 3.0,
        bundle_top - cradle_thickness + 0.2,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    body = back + cradle + rail

    # M4 clearance bore, normal to the wall.  The 3 mm back gives the screw
    # 2.4 mm of guided material before its head seats at the front face.
    screw_hole = Pos(-0.2, run / 2.0, 18.0) * Rot(0, 90, 0) * Cylinder(
        2.2,
        back_thickness + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - screw_hole

    if draft:
        return body

    # The rail and cradle edges are intentionally square: they are the measured
    # retention stops, and polishing them would introduce sub-millimetre slivers.
    return body
