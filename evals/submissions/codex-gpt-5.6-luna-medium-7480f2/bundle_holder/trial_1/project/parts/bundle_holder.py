from nurb import *


def _box(x, y, z, length, width, height):
    """A box specified by its minimum corner, rather than its centre."""
    return Pos(x + length / 2, y + width / 2, z + height / 2) * Box(length, width, height)


@part
def bundle_holder(bundle_diameter=8.0, length=16.0, draft=False):
    """Wall-mounted cable-bundle holder, printed flat with the back at X=0.

    bundle_diameter: measured diameter of the cable bundle
    length: holder length along the bundle, parallel to Y
    """
    clearance = 0.4
    bundle = bundle_diameter + clearance

    back_thickness = 2.4
    shelf_thickness = 2.4
    front_thickness = 1.4
    # Keep the bundle 0.2 mm off each wall while retaining the requested envelope.
    channel_width = bundle + 0.2
    channel_height = bundle + 0.2
    channel_x = back_thickness + 0.2
    channel_z = shelf_thickness + 0.2

    back = _box(0, 0, 0, back_thickness, length, 20.0)
    shelf = _box(
        back_thickness,
        0,
        0,
        channel_x + channel_width - back_thickness,
        length,
        shelf_thickness,
    )
    front = _box(
        channel_x + channel_width,
        0,
        0,
        front_thickness,
        length,
        channel_height + shelf_thickness,
    )
    body = back + shelf + front

    # M4 clearance bore, normal to the wall.  The back is deliberately 2.4 mm
    # thick so the screw head seats immediately on its front face.
    screw_bore = Pos(back_thickness / 2, length / 2, 16.0) * Rot(0, 90, 0) * Cylinder(2.2, back_thickness)
    body = body - screw_bore

    # The fit channel is deliberately left sharp: chamfering its inside edges
    # would reduce the measured retention envelope and the print-critical walls.
    return body
