from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    screw_hole_diameter=4.2,
    draft=False,
):
    """
    bundle_diameter: diameter of the cable bundle the channel holds
    wall_thickness: thickness of the channel walls, each side
    base_thickness: thickness of the solid floor under the channel
    clip_length: how far the clip runs along the cable
    tab_length: how far the mounting tab reaches out past the wall
    screw_hole_diameter: diameter of the screw hole through the tab
    """
    channel_width = bundle_diameter + 0.4
    channel_depth = bundle_diameter

    body_width = channel_width + 2 * wall_thickness
    body_height = base_thickness + channel_depth

    overshoot = 2.0

    body = Box(body_width, clip_length, body_height, align=(Align.MIN, Align.MIN, Align.MIN))

    # Overshoots the top and both Y ends so the cut cleanly opens the channel's
    # top and both ends rather than leaving coincident, boolean-fragile faces.
    channel_cut = Pos(wall_thickness, -overshoot, base_thickness) * Box(
        channel_width,
        clip_length + 2 * overshoot,
        channel_depth + overshoot,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    tab = Pos(-tab_length, 0, 0) * Box(
        tab_length, clip_length, base_thickness, align=(Align.MIN, Align.MIN, Align.MIN)
    )

    hole = Pos(-tab_length / 2, clip_length / 2, -overshoot) * Cylinder(
        screw_hole_diameter / 2,
        base_thickness + 2 * overshoot,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    solid = body + tab - channel_cut - hole

    if draft:
        return solid

    # The channel is fit-critical mating geometry (a lead-in chamfer at its mouth
    # would deform the cable seat), so nothing bordering its cavity gets touched,
    # on top of the usual bottom-face and concave exclusions.
    bed = solid.bounding_box().min.Z
    concave = set(concave_edges(solid))
    channel_x_min = wall_thickness
    channel_x_max = wall_thickness + channel_width

    def in_channel(edge):
        bb = edge.bounding_box()
        return (
            bb.min.Z >= base_thickness - 1e-4
            and bb.min.X >= channel_x_min - 1e-4
            and bb.max.X <= channel_x_max + 1e-4
        )

    def is_tab_step_post(edge):
        # The wall's outer corner post above the tab (X=0) starts at the tab's
        # top, not the bed, so it escapes the bottom-face filter. Chamfering it
        # meets the two rim edges at a convex vertex and leaves a sub-mm sliver
        # triangle that its twin on the tabless wall never forms, because that
        # one *does* run to the bed and is excluded outright.
        bb = edge.bounding_box()
        return (
            bb.max.X - bb.min.X < 1e-6
            and bb.max.Y - bb.min.Y < 1e-6
            and abs(bb.min.X) < 1e-6
        )

    def keep_edge(e):
        bb = e.bounding_box()
        if bb.min.Z <= bed + 1e-6:
            return False
        if e in concave:
            return False
        if in_channel(e):
            return False
        if is_tab_step_post(e):
            return False
        if e.is_closed:
            # The screw hole's rim: a chamfer here widens the top opening right
            # where the tab is at its thinnest, and thins the section next to it
            # below what the printer lays down reliably. Leave the hole square.
            return False
        return True

    keep = solid.edges().filter_by(keep_edge)
    return polish(solid, keep, 1.0)
