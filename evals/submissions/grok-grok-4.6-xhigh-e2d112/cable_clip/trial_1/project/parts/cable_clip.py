from nurb import *

WALL = 2.4
BASE = 3.0
LENGTH = 12.0
TAB = 10.0
HOLE = 4.2
CLEARANCE = 0.4


@part
def cable_clip(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Screw-down clip that holds a cable bundle against a surface.

    bundle_diameter: measured across the taped cable bundle; sets channel width and depth
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 2mm: raise it so the channel can print",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + CLEARANCE
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * WALL
    height = BASE + channel_depth
    hole_x = body_width + TAB / 2.0
    hole_r = HOLE / 2.0

    body = Box(body_width, LENGTH, height, align=(Align.MIN, Align.CENTER, Align.MIN))
    channel = Pos(WALL, 0, BASE) * Box(
        channel_width,
        LENGTH + 2,
        channel_depth + 1,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    tab = Pos(body_width, 0, 0) * Box(
        TAB, LENGTH, BASE, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    hole = Pos(hole_x, 0, -1) * Cylinder(
        hole_r, BASE + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    body = (body - channel) + tab - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)

    def lies_in_bed(edge):
        bb = edge.bounding_box()
        return abs(bb.min.Z - bed) < 1e-4 and abs(bb.max.Z - bed) < 1e-4

    def in_channel(edge):
        bb = edge.bounding_box()
        in_x = bb.min.X >= WALL - 1e-4 and bb.max.X <= WALL + channel_width + 1e-4
        at_or_above_floor = bb.min.Z >= BASE - 1e-4
        return in_x and at_or_above_floor

    def on_hole(edge):
        mid = edge @ 0.5
        radial = ((mid.X - hole_x) ** 2 + (mid.Y - 0.0) ** 2) ** 0.5
        return abs(radial - hole_r) < 0.2

    def along_y(edge):
        # Skip Y-end edges: 1mm chamfers on all three corner edges leave 0.87mm2 slivers.
        bb = edge.bounding_box()
        return bb.max.Y - bb.min.Y > 5.0

    keep = body.edges().filter_by(
        lambda e: (
            e not in concave
            and not lies_in_bed(e)
            and not in_channel(e)
            and not on_hole(e)
            and along_y(e)
        )
    )
    return polish(body, keep, 1.0)
