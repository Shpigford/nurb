from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    cable_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_width=4.2,
    draft=False,
):
    """A screw-down clip that traps a cable bundle in an open-top channel.

    bundle_diameter: how thick the cable bundle is where the clip grips it
    cable_clearance: slack added across the channel so the bundle drops in
    wall_thickness: how thick each side wall of the channel is
    base_thickness: how much material sits under the cable, and how thick the tab is
    clip_length: how far the clip runs along the cable
    tab_length: how far the screw tab sticks out past the wall
    screw_hole_width: diameter of the screw hole through the tab
    """
    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    body = Pos(body_width / 2, 0, height / 2) * Box(body_width, clip_length, height)

    # Open-top channel, cut clean through both ends and out of the top.
    channel = Pos(
        wall_thickness + channel_width / 2,
        0,
        base_thickness + channel_depth,
    ) * Box(channel_width, clip_length + 2, 2 * channel_depth)

    tab = Pos(
        body_width + tab_length / 2,
        0,
        base_thickness / 2,
    ) * Box(tab_length, clip_length, base_thickness)

    hole_x = body_width + tab_length / 2
    hole = Pos(hole_x, 0, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness + 2
    )

    solid = (body - channel) + tab - hole

    if draft:
        return solid

    # Name what must stay sharp, then let `polish` chamfer whatever the kernel takes.
    eps = 0.01
    concave = concave_edges(solid)

    def is_concave(e):
        return any(e.is_same(c) for c in concave)

    def in_channel(e):
        # Anything the channel owns: its flat floor, its inner walls, its mouth, and
        # the wall-top edges that merely reach it, whose chamfer would nick the bore.
        bb = e.bounding_box()
        return (
            bb.max.X > wall_thickness - eps
            and bb.min.X < wall_thickness + channel_width + eps
            and bb.min.Z > base_thickness - eps
        )

    def at_screw_hole(e):
        bb = e.bounding_box()
        return (
            abs(bb.center().X - hole_x) < eps
            and bb.size.X < screw_hole_width + eps
            and bb.size.Y < screw_hole_width + eps
        )

    def lies_on_bed(e):
        return e.bounding_box().max.Z < eps

    keep = solid.edges().filter_by(
        lambda e: not (
            lies_on_bed(e) or is_concave(e) or in_channel(e) or at_screw_hole(e)
        )
    )
    # 1.2 rather than the usual 1.0: three chamfers meet at each outer tab corner, and
    # the triangle they leave is 0.866 * size**2. At 1.0 that is a 0.87mm2 sliver; at
    # 1.2 it is 1.25mm2, a face the part can own rather than a baseline to accept.
    return polish(solid, keep, 1.2)
