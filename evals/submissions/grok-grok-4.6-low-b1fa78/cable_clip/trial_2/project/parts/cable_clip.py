from nurb import *


@part
def cable_clip(bundle_diameter=8.0, draft=False):
    """Screw-down clip for a taped cable bundle.

    bundle_diameter: measured width of the cable bundle; channel width and depth follow it.
    """
    clearance = 0.4
    wall = 2.4
    base = 3.0
    length = 12.0
    tab_length = 10.0
    hole_dia = 4.2

    channel_w = bundle_diameter + clearance
    channel_d = bundle_diameter
    body_w = channel_w + 2 * wall
    height = base + channel_d

    body = Box(body_w, length, height, align=(Align.MIN, Align.MIN, Align.MIN))
    tab = Box(tab_length, length, base, align=(Align.MIN, Align.MIN, Align.MIN))
    tab = tab.moved(Location((body_w, 0, 0)))
    clip = body + tab

    channel = Box(channel_w, length, channel_d, align=(Align.MIN, Align.MIN, Align.MIN))
    channel = channel.moved(Location((wall, 0, base)))
    clip = clip - channel

    hole = Cylinder(hole_dia / 2, base, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hole = hole.moved(Location((body_w + tab_length / 2, length / 2, 0)))
    clip = clip - hole

    # Channel and tab-to-wall junctions must stay square; chamfering them
    # thins the 2.4 mm walls and the 3 mm tab. Leave the solid as modelled.
    return clip
