from nurb import *


@part
def cable_clip(bundle_diameter=float(measured("bundle_diameter")), draft=False):
    """Screw-down clip that holds a taped cable bundle against a surface.

    bundle_diameter: measured width of the cable bundle the open channel holds
    """
    clearance = 0.4
    wall = 2.4
    base = 3.0
    length = 12.0
    tab_length = 10.0
    hole_dia = 4.2

    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 2mm: the channel "
            "would print closed. Raise it to 2 or more.",
            param="bundle_diameter",
        )

    channel_w = bundle_diameter + clearance
    channel_d = bundle_diameter
    body_w = channel_w + 2 * wall
    total_w = body_w + tab_length

    plate = Box(total_w, length, base, align=(Align.MIN, Align.MIN, Align.MIN))
    left = Pos(0, 0, base) * Box(
        wall, length, channel_d, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    right = Pos(wall + channel_w, 0, base) * Box(
        wall, length, channel_d, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    body = plate + left + right

    hole = Pos(body_w + tab_length / 2, length / 2, -1) * Cylinder(
        hole_dia / 2,
        base + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - hole

    if draft:
        return body

    # Channel stays square. Skip the bed face, the hole, concave
    # junctions, and the Y-end profile (those last, plus the long and
    # vertical edges, make the 0.87mm2 corner slivers).
    bed = body.bounding_box().min.Z
    x0, x1 = wall, wall + channel_w
    z_floor = base

    def lies_in_bed(edge):
        return edge.bounding_box().max.Z <= bed + 1e-6

    def in_channel(edge):
        bb = edge.bounding_box()
        on_floor = (
            abs(bb.min.Z - z_floor) < 1e-4
            and abs(bb.max.Z - z_floor) < 1e-4
            and bb.min.X >= x0 - 1e-4
            and bb.max.X <= x1 + 1e-4
        )
        on_inner = (
            (abs(bb.min.X - x0) < 1e-4 and abs(bb.max.X - x0) < 1e-4)
            or (abs(bb.min.X - x1) < 1e-4 and abs(bb.max.X - x1) < 1e-4)
        ) and bb.min.Z >= z_floor - 1e-4
        return on_floor or on_inner

    def is_circle(edge):
        return edge.geom_type == GeomType.CIRCLE

    def on_end_face(edge):
        bb = edge.bounding_box()
        return (bb.max.Y - bb.min.Y) < 1e-4

    keep = body.edges().filter_by(
        lambda e: not lies_in_bed(e)
        and not in_channel(e)
        and not is_circle(e)
        and not on_end_face(e)
    )
    keep = keep - concave_edges(body)
    return polish(body, keep, 1.0)
