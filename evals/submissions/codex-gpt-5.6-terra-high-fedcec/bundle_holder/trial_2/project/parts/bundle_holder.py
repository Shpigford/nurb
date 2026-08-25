from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """A compact, wall-mounted through-holder for a horizontal cable bundle.

    bundle_diameter: measured diameter of the cable bundle passing through the holder
    """
    # The channel deliberately has 0.6 mm total slack at its two retaining faces.
    clearance = 0.4
    channel_diameter = bundle_diameter + clearance
    wall_thickness = 3.0
    length = 12.6
    # Keep a stable 0.3 mm wall-side gap as the requested bundle size changes.
    bundle_x = wall_thickness + bundle_diameter / 2 + 0.5
    bundle_z = bundle_diameter + 4.5
    # The ramp is tangent to the 8.4 mm clearance envelope.  Either a down or
    # forward 1 mm motion moves the bundle 0.71 mm closer to this 45 degree face.
    ramp_intercept = bundle_z - bundle_x - (channel_diameter / 2) * 2**0.5

    # A broad plate is the wall contact.  The 45 degree ramp is fully grounded,
    # prints without a ceiling, and captures the cable in both required directions.
    back = Box(wall_thickness, length, 17.0,
               align=(Align.MIN, Align.MIN, Align.MIN))
    ramp_start = wall_thickness
    ramp_end = 15.0
    # Polygon is drawn in local X/-Z, extruded locally in +Z, then rotated so
    # that the extrusion becomes the holder's Y length.
    ramp_profile = Polygon(
        (ramp_start, 0), (ramp_end, 0),
        (ramp_end, -(ramp_end + ramp_intercept)),
        (ramp_start, -(ramp_start + ramp_intercept)),
    )
    ramp = Pos(0, length, 0) * Rot(-90, 0, 0) * extrude(ramp_profile, amount=length)
    body = back + ramp

    # This open-sided throat is the clearance envelope for the cable.  It also
    # removes the roof of the screw-driver pocket, so the part remains support-free.
    channel_floor = bundle_z - channel_diameter / 2 - 0.3
    channel_front = bundle_x + channel_diameter / 2 + 0.1
    channel_open = Pos(wall_thickness, 0, channel_floor) * Box(
        channel_front - wall_thickness, length, 20.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body = body - channel_open

    # M4 clearance bore from the wall, followed by a generous pan-head and
    # driver escape.  Keeping its centre low leaves the cable's 8 mm envelope
    # clear of the installed screw.
    bore = Pos(0, 4.2, 4.0) * Cylinder(
        2.2, 16.0, rotation=(0, 90, 0),
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # An open driver chimney is wider than the 8.4 mm pan-head envelope and
    # deliberately reaches the top: it cannot trap a driver under a printed roof.
    driver_escape = Pos(wall_thickness, 0, 0) * Box(
        16.0, 8.4, 20.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    body = body - bore - driver_escape

    return body
