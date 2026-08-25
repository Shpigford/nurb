from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    wall=2.4,
    base=3.0,
    tab_length=10.0,
    part_length=12.0,
    hole_diameter=4.2,
    clearance=0.4,
    draft=False,
):
    """
    bundle_diameter: the cable bundle's diameter the channel wraps around
    wall: channel wall thickness on each side
    base: material under the channel, and the mounting tab's thickness
    tab_length: how far the mounting tab reaches out past the channel wall
    part_length: how long the clip runs along the cable
    hole_diameter: the screw's through-hole in the mounting tab
    clearance: extra channel width over the bundle so the cable drops in without binding
    """
    if bundle_diameter <= 0:
        reject(f"bundle_diameter {bundle_diameter} must be positive", param="bundle_diameter")

    channel_width = bundle_diameter + clearance
    channel_depth = bundle_diameter
    block_width = channel_width + 2 * wall
    total_height = base + channel_depth
    total_width = block_width + tab_length

    slab = Pos(total_width / 2, part_length / 2, base / 2) * Box(total_width, part_length, base)

    left_wall = Pos(wall / 2, part_length / 2, base + channel_depth / 2) * Box(wall, part_length, channel_depth)
    right_wall_x = wall + channel_width + wall / 2
    right_wall = Pos(right_wall_x, part_length / 2, base + channel_depth / 2) * Box(
        wall, part_length, channel_depth
    )

    tab_center_x = block_width + tab_length / 2
    hole = Pos(tab_center_x, part_length / 2, base / 2) * Cylinder(hole_diameter / 2, base + 2.0)

    body = slab + left_wall + right_wall - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    eps = 1e-6
    concave = concave_edges(body)

    def on_bottom(e):
        return e.bounding_box().max.Z <= bed + eps

    def in_channel(e):
        # The channel's floor and inner walls: fit-critical, never a lead-in chamfer.
        bb = e.bounding_box()
        return (
            bb.min.X >= wall - eps
            and bb.max.X <= wall + channel_width + eps
            and bb.min.Z >= base - eps
            and bb.max.Z <= total_height + eps
        )

    def end_cap_connector(e):
        # The short horizontal edge tying a vertical corner chamfer to the long edge
        # above it, at each Y end. Chamfering it too turns every outer corner into a
        # trihedral collision that leaves a sub-1mm2 cap triangle; drop it and the
        # vertical and long edges still meet cleanly on their own.
        bb = e.bounding_box()
        on_end = abs(bb.min.Y - bb.max.Y) < eps and (
            abs(bb.min.Y - 0) < eps or abs(bb.min.Y - part_length) < eps
        )
        horizontal = bb.max.Z - bb.min.Z < eps
        return on_end and horizontal

    keep = body.edges().filter_by(
        lambda e: not on_bottom(e)
        and not in_channel(e)
        and not end_cap_connector(e)
        and e not in concave
        and e.geom_type != GeomType.CIRCLE
    )
    return polish(body, keep, 1.0)
