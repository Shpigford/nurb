from nurb import *


@part
def bundle_holder(bundle_diameter: float = measured("bundle_diameter"), draft=False):
    """Wall holder for a horizontal cable bundle.

    bundle_diameter: measured cable bundle diameter
    """
    clearance = 0.4
    channel_diameter = bundle_diameter + 2.0 * clearance

    # The bundle sits in the open channel, centered between the two rails.
    # All members are grounded in Z and fuse into the back plate.
    back = Pos(1.25, 0, 10) * Box(2.5, 17, 20)
    lower_rail = Pos(8.5, 0, 4.0) * Box(12.0, 17, 8.0)
    upper_rail = Pos(8.5, 0, 19.0) * Box(12.0, 17, 2.0)
    front_stop = Pos(13.25, 0, 13.0) * Box(2.5, 17, 10.0)
    body = back + lower_rail + upper_rail + front_stop

    # M4 medium-clearance bore, normal to the wall, with a 4.4 mm opening.
    screw_bore = Pos(1.25, 0, 3.5) * Rot(0, 90, 0) * Cylinder(2.2, 4.0)
    body = body - screw_bore

    return body
