from nurb import *


@part
def cable_clip(bundle_diameter=float(measured("bundle_diameter")), draft=False):
    """Screw-down clip for a cable bundle along Y.

    bundle_diameter: measured cable bundle across, in mm. Channel width is this
    plus 0.4 mm clearance; channel depth matches the bundle.
    """

    clearance = 0.4
    wall = 2.4
    base = 3.0
    length = 12.0
    tab_length = 10.0
    hole_dia = 4.2

    inner_w = bundle_diameter + clearance
    inner_h = bundle_diameter
    channel_outer = inner_w + 2 * wall
    height = base + inner_h
    total_x = channel_outer + tab_length

    body = Box(channel_outer, length, height).moved(Location((channel_outer / 2, 0, height / 2)))
    channel = Box(inner_w, length + 2, inner_h + 1).moved(
        Location((wall + inner_w / 2, 0, base + inner_h / 2 + 0.5))
    )
    body = body - channel

    tab = Box(tab_length, length, base).moved(
        Location((channel_outer + tab_length / 2, 0, base / 2))
    )
    clip = body + tab

    hole = Cylinder(hole_dia / 2, base + 2).moved(
        Location((channel_outer + tab_length / 2, 0, base / 2))
    )
    clip = clip - hole

    return clip
