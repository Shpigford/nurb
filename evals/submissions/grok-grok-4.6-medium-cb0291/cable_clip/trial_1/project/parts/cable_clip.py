from nurb import *

WALL = 2.4
BASE = 3.0
LENGTH = 12.0
TAB_LENGTH = 10.0
HOLE_DIA = 4.2
CHANNEL_CLEARANCE = 0.4


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle in an open channel.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    channel_width = bundle_diameter + CHANNEL_CLEARANCE
    channel_depth = bundle_diameter
    body_width = 2 * WALL + channel_width
    height = BASE + channel_depth

    body = Box(body_width, LENGTH, height, align=(Align.MIN, Align.MIN, Align.MIN))
    slot = Box(
        channel_width,
        LENGTH + 2,
        channel_depth + 1,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).locate(Location((WALL, -1, BASE)))
    body = body - slot

    tab = Box(
        TAB_LENGTH, LENGTH, BASE, align=(Align.MIN, Align.MIN, Align.MIN)
    ).locate(Location((body_width, 0, 0)))
    body = body + tab

    hole = Cylinder(
        HOLE_DIA / 2,
        BASE + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).locate(Location((body_width + TAB_LENGTH / 2, LENGTH / 2, -1)))
    body = body - hole

    if draft:
        return body
    # Channel floor and inner corners stay square. A 1mm polish on the 2.4mm
    # wall tops or the tab/wall L makes slivers and concave_cosmetic strips.
    return body
