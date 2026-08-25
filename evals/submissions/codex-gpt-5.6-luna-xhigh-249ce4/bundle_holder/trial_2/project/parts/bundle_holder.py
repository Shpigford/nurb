from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall holder for a cable bundle.

    bundle_diameter: measured diameter of the bundle being retained
    """
    clearance = 0.4
    bundle_space = bundle_diameter + clearance

    # The holder prints on its broad XY footprint.  X is away from the wall,
    # Y is the cable run, and Z remains vertical after mounting.
    run_length = 14.0
    back_thickness = 3.0
    back_height = 21.0
    shelf_thickness = 2.0
    retainer_thickness = 2.0
    side_gap = 0.6

    front_inner_x = back_thickness + bundle_space + side_gap
    front_outer_x = front_inner_x + retainer_thickness
    retainer_top = shelf_thickness + bundle_space + 1.0

    back = Box(
        back_thickness,
        run_length,
        back_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    shelf = Box(
        front_outer_x,
        run_length,
        shelf_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    retainer = Pos(front_inner_x, 0, shelf_thickness) * Box(
        retainer_thickness,
        run_length,
        retainer_top - shelf_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    body = back + shelf + retainer
    if draft:
        return body

    # M4 clearance through the 3 mm back plate.  The seat is the front face
    # of the plate; the screw head is above the cable channel and clears the
    # retaining rail.
    screw_hole = Pos(-0.1, run_length / 2.0, 17.5) * Cylinder(
        2.2,
        back_thickness + 0.2,
        rotation=(0, 90, 0),
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body - screw_hole
