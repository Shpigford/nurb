from nurb import *

WALL = 2.4
BASE = 3.0
LENGTH = 12.0
TAB_LENGTH = 10.0
TAB_THICKNESS = 3.0
HOLE_DIA = 4.2
CHANNEL_CLEARANCE = 0.4


@part
def cable_clip(bundle_diameter=measured("bundle_diameter")):
    """Screw-down clip that holds a cable bundle.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    channel_width = bundle_diameter + CHANNEL_CLEARANCE
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * WALL
    height = BASE + channel_depth
    total_x = body_width + TAB_LENGTH

    profile = Plane.XZ * Polygon(
        (0, 0),
        (total_x, 0),
        (total_x, TAB_THICKNESS),
        (body_width, TAB_THICKNESS),
        (body_width, height),
        (body_width - WALL, height),
        (body_width - WALL, BASE),
        (WALL, BASE),
        (WALL, height),
        (0, height),
    )
    body = extrude(profile, LENGTH, dir=(0, 1, 0))

    hole_x = body_width + TAB_LENGTH / 2
    hole_y = LENGTH / 2
    body -= Pos(hole_x, hole_y, TAB_THICKNESS / 2) * Cylinder(
        HOLE_DIA / 2, TAB_THICKNESS + 2
    )

    return body
