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
    chamfer_size=1.2,
    draft=False,
):
    """A screw-down clip that traps a cable bundle in an open-top channel.

    bundle_diameter: how thick the cable bundle is, measured across
    cable_clearance: extra channel width over the bundle, so it drops in
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable, and how thick the tab is
    clip_length: how far the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    screw_hole_width: diameter of the screw hole through the tab
    chamfer_size: how big the chamfers on the outside edges are
    """
    if bundle_diameter <= 0:
        reject("bundle_diameter has to be a real width across the bundle", param="bundle_diameter")
    if screw_hole_width + 2 * chamfer_size >= min(tab_length, clip_length):
        reject(
            f"screw_hole_width {screw_hole_width} leaves no tab around it: "
            f"raise tab_length above {screw_hole_width + 4:.1f}",
            param="screw_hole_width",
        )

    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth
    tab_center_x = body_width + tab_length / 2

    body = Pos(body_width / 2, clip_length / 2, height / 2) * Box(body_width, clip_length, height)
    channel = Pos(
        body_width / 2, clip_length / 2, base_thickness + (channel_depth + 2) / 2
    ) * Box(channel_width, clip_length + 4, channel_depth + 2)
    tab = Pos(tab_center_x, clip_length / 2, base_thickness / 2) * Box(
        tab_length, clip_length, base_thickness
    )
    screw_hole = Pos(tab_center_x, clip_length / 2, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness * 3
    )

    solid = (body - channel) + tab - screw_hole
    if draft:
        return solid

    # The channel is the mating surface: no lead-in chamfer at its mouth, and its floor
    # stays one flat face the full width. The screw bore keeps its modelled diameter.
    bed = solid.bounding_box().min.Z
    concave = concave_edges(solid)
    bore_radius = screw_hole_width / 2 + 1e-6

    def outside_the_channel(e):
        bb = e.bounding_box()
        touches_channel = (
            bb.max.X > wall_thickness - 1e-6
            and bb.min.X < wall_thickness + channel_width + 1e-6
        )
        return not (touches_channel and bb.max.Z > base_thickness - 1e-6)

    def off_the_bore(e):
        bb = e.bounding_box()
        return not (
            abs(bb.center().X - tab_center_x) < 1e-6
            and abs(bb.center().Y - clip_length / 2) < 1e-6
            and max(bb.size.X, bb.size.Y) < 2 * bore_radius + 1e-3
        )

    keep = [
        e
        for e in solid.edges()
        if e.bounding_box().max.Z > bed + 1e-6
        and e not in concave
        and outside_the_channel(e)
        and off_the_bore(e)
    ]
    return polish(solid, keep, chamfer_size)
