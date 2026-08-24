from nurb import *


@part
def cable_clip(
    bundle_diameter=float(measured("bundle_diameter")),
    draft=False,
):
    """Screw-down clip for a taped cable bundle.

    bundle_diameter: across the cable bundle the channel holds
    """
    wall = 2.4
    base = 3.0
    length = 12.0
    tab_length = 10.0
    hole_dia = 4.2
    channel_clearance = 0.4

    channel_w = bundle_diameter + channel_clearance
    channel_d = bundle_diameter
    clip_w = channel_w + 2 * wall
    clip_h = base + channel_d

    body = Box(clip_w, length, clip_h)

    tab = Box(tab_length, length, base)
    tab = loc(tab, (clip_w / 2 + tab_length / 2, 0, -clip_h / 2 + base / 2))

    part_solid = body + tab

    cut = Box(channel_w, length + 2, channel_d + 1)
    cut = loc(cut, (0, 0, (base + 1) / 2))
    part_solid = part_solid - cut

    hole = Cylinder(hole_dia / 2, base + 2)
    hole = loc(hole, (clip_w / 2 + tab_length / 2, 0, -clip_h / 2 + base / 2))
    part_solid = part_solid - hole

    return part_solid


def loc(shape, xyz):
    return shape.moved(Location(xyz))
