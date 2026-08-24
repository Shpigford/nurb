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
    """Screw-down clip that holds a cable bundle against a surface.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is too small for a printable channel; raise it above 2.0",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + CHANNEL_CLEARANCE
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * WALL
    height = BASE + channel_depth

    profile = Plane.XZ * Polygon(
        (0, 0),
        (body_width + TAB_LENGTH, 0),
        (body_width + TAB_LENGTH, TAB_THICKNESS),
        (body_width, TAB_THICKNESS),
        (body_width, height),
        (body_width - WALL, height),
        (body_width - WALL, BASE),
        (WALL, BASE),
        (WALL, height),
        (0, height),
    )
    clip = extrude(profile, amount=LENGTH)
    bb = clip.bounding_box()
    clip = clip.move(Location((-bb.min.X, -bb.min.Y, -bb.min.Z)))

    hole_x = body_width + TAB_LENGTH / 2.0
    hole_y = LENGTH / 2.0
    hole = Cylinder(
        HOLE_DIA / 2.0,
        TAB_THICKNESS + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).move(Location((hole_x, hole_y, -1.0)))
    clip = clip - hole

    if draft:
        return clip
    return clip
