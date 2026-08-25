from nurb import *


WALL = 2.4
BASE = 3.0
LENGTH = 12.0
TAB_LENGTH = 10.0
HOLE_DIA = 4.2
CHANNEL_CLEARANCE = 0.4
POLISH = 1.0


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle in an open-top channel.

    bundle_diameter: measured width of the cable bundle the channel holds
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter}mm is too small for a printable "
            "channel; raise it above 2.0",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + CHANNEL_CLEARANCE
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * WALL
    tab_x = body_width

    plate = Box(
        body_width + TAB_LENGTH,
        LENGTH,
        BASE,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Pos(0, 0, BASE) * Box(
        WALL, LENGTH, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    right_wall = Pos(WALL + channel_width, 0, BASE) * Box(
        WALL, LENGTH, channel_depth, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    clip = plate + left_wall + right_wall

    hole = Pos(tab_x + TAB_LENGTH / 2, LENGTH / 2, -1) * Cylinder(
        HOLE_DIA / 2,
        BASE + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    clip = clip - hole

    if draft:
        return clip

    bed = clip.bounding_box().min.Z
    inner_left = WALL
    inner_right = WALL + channel_width
    inside = set(concave_edges(clip))

    def exposed(edge):
        if edge in inside:
            return False
        # Circles (the screw hole) chamfer into a knife the min-wall probe reads.
        if edge.geom_type != GeomType.LINE:
            return False
        bb = edge.bounding_box()
        if bb.min.Z <= bed + 1e-4:
            return False
        # Verticals plus rims meet in 0.87mm2 corner triangles; rims only.
        if bb.max.Z - bb.min.Z > 1e-3:
            return False
        if edge.length < 3.0:
            return False
        c = edge.center()
        # Leave the U-channel square: floor, inner walls, and both open mouths.
        if inner_left - 1e-4 <= c.X <= inner_right + 1e-4 and c.Z >= BASE - 1e-4:
            return False
        return True

    keep = clip.edges().filter_by(exposed)
    return polish(clip, keep, POLISH)
