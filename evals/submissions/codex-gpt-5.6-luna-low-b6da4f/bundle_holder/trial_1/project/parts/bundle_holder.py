from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """Wall holder for a horizontal cable bundle.

    bundle_diameter: diameter of the cable bundle clearance
    """
    clearance = bundle_diameter + 0.4
    length = 20.0
    back_height = 14.0
    back_thickness = 2.8
    back = Box(back_thickness, length, back_height,
               align=(Align.MIN, Align.MIN, Align.MIN))
    rail_y = 7.0
    rail_x = 11.2
    rail_thickness = 2.0
    bundle_bottom = 1.8
    bundle_top = bundle_bottom + clearance
    lower = Pos(2.5, 7.0, 0) * Box(rail_x, rail_y, bundle_bottom,
                                               align=(Align.MIN, Align.MIN, Align.MIN))
    upper = Pos(2.5, 7.0, bundle_top) * Box(rail_x, rail_y, rail_thickness,
                                                         align=(Align.MIN, Align.MIN, Align.MIN))
    side = Pos(12.0, 7.0, 0) * Box(2.0, rail_y, 12.0,
                                    align=(Align.MIN, Align.MIN, Align.MIN))
    body = back + lower + upper + side
    bore = Pos(0, 3.0, 10.5) * Cylinder(2.2, 8.0, rotation=(0, 90, 0),
                                           align=(Align.MIN, Align.CENTER, Align.CENTER))
    body = body - bore
    # Fit-critical rails and the counterbore stay sharp; the compact profile
    # is intentionally left un-dressed so no cosmetic edge can affect fit.
    return body
