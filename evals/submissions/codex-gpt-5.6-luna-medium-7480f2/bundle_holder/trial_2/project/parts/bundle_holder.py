from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter")):
    """Wall holder for a horizontal cable bundle.

    bundle_diameter: measured cable bundle diameter
    """
    # The wall is the minimum-X face.  All dimensions are derived from the
    # measured bundle so the 0.4 mm fit clearance follows nearby sizes.
    length = 12.0
    back_thickness = 3.0
    fit_diameter = bundle_diameter + 0.4
    guard_x = back_thickness + fit_diameter
    bundle_center_x = back_thickness + fit_diameter / 2.0

    back = Box(
        back_thickness, length, 21.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    shelf = Box(
        guard_x + 3.0, length, 3.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    # The guard is a grounded side wall.  The cable envelope ends 0.2 mm
    # before it at rest, while the wall blocks the required outward motion.
    guard = Pos(guard_x, 0.0, 3.0) * Box(
        3.0, length, 9.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    body = back + shelf + guard

    # M4 medium clearance bore, normal to the wall.  It opens on the back
    # face and seats at x=3; the head has open space forward of that seat.
    screw_bore = Pos(0.0, length / 2.0, 17.0) * Rot(0, 90, 0) * Cylinder(
        2.2, back_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - screw_bore

    # Keep the functional edges square; this avoids reducing the fit envelope
    # and keeps the entire print on its flat bed face.
    return body
