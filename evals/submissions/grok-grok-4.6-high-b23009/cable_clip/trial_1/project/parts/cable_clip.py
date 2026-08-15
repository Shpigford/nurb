from nurb import *

WALL = 2.4
BASE = 3.0
LENGTH = 12.0
TAB_LENGTH = 10.0
TAB_THICKNESS = 3.0
HOLE_DIA = 4.2
CHANNEL_CLEARANCE = 0.4


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle in an open channel.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 2mm: raise it to at least 2",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + CHANNEL_CLEARANCE
    channel_depth = bundle_diameter
    body_width = WALL + channel_width + WALL
    body_height = BASE + channel_depth

    body = Box(
        body_width,
        LENGTH,
        body_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    channel = Box(
        channel_width,
        LENGTH,
        channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((WALL, 0, BASE)))
    clip = body - channel

    tab = Box(
        TAB_LENGTH,
        LENGTH,
        TAB_THICKNESS,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((body_width, 0, 0)))
    hole = Cylinder(
        HOLE_DIA / 2,
        TAB_THICKNESS + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((body_width + TAB_LENGTH / 2, LENGTH / 2, -1)))
    # Channel floor stays one flat face the full width: no polish inside
    # the channel, and no dress-up chamfers that thin the tab or walls.
    return clip + tab - hole
