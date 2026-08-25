from nurb import *

WALL = 2.4
BASE = 3.0
LENGTH = 12.0
TAB_LENGTH = 10.0
HOLE_DIA = 4.2
CHANNEL_CLEARANCE = 0.4


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle in an open-top channel.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    if bundle_diameter <= 0:
        reject(
            f"bundle_diameter {bundle_diameter} must be greater than 0",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + CHANNEL_CLEARANCE
    channel_depth = bundle_diameter
    channel_outer = channel_width + 2 * WALL

    slab = Box(
        channel_outer + TAB_LENGTH,
        LENGTH,
        BASE,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Box(
        WALL, LENGTH, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN)
    ).move(Location((0, 0, BASE)))
    right_wall = Box(
        WALL, LENGTH, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN)
    ).move(Location((WALL + channel_width, 0, BASE)))

    hole = Cylinder(
        HOLE_DIA / 2,
        BASE + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).move(Location((channel_outer + TAB_LENGTH / 2, LENGTH / 2, -1)))

    # Channel inner corners stay square: no polish on the mating channel,
    # and no outer chamfers either — they thin the tab around the screw
    # hole and leave cosmetic strips at the wall-to-tab junction.
    return slab + left_wall + right_wall - hole
