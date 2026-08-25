from nurb import *


@part
def pole_rest(pole_diameter=measured("pole_diameter"), length=20.0, clearance=0.2):
    """A support-free drying cradle for a finished pole.

    pole_diameter: measured diameter of the pole being supported
    length: length of the rest along the pole
    clearance: radial breathing room around the soft finished surface
    """
    if pole_diameter <= 0.0:
        reject("pole_diameter must be positive", param="pole_diameter")

    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + clearance
    axis_height = 18.0
    side_backing = 1.4
    body_width = 2.0 * (seat_radius + side_backing)
    body_height = axis_height + 2.0

    # A broad, low rectangular body is opened into a circular lower bowl and a
    # straight vertical throat.  The throat is deliberately at least pole-wide:
    # it lets the pole descend vertically while the lower semicircle cradles it.
    body = Box(body_width, length, body_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bore = Cylinder(seat_radius, length + 2.0, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.CENTER)).moved(Location((0, 0, axis_height)))
    throat = Box(2.0 * seat_radius, length + 2.0, body_height - axis_height + 1.0,
                 align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, axis_height)))
    return body - bore - throat
