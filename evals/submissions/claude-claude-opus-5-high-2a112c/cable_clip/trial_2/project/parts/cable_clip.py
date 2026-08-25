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
    chamfer_size=1.0,
    draft=False,
):
    """A screw-down clip that traps a cable bundle in an open-top channel.

    bundle_diameter: how thick the cable bundle is; the channel is sized from it
    cable_clearance: extra width in the channel so the bundle drops in
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable, and how thick the tab is
    clip_length: how far the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    screw_hole_width: diameter of the through-hole for the mounting screw
    chamfer_size: how much is taken off the exposed outside edges
    """
    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = channel_width + 2 * wall_thickness
    height = base_thickness + channel_depth

    if screw_hole_width + 2 * chamfer_size >= tab_length:
        reject(
            f"screw_hole_width {screw_hole_width} leaves no tab around it: "
            f"keep it under {tab_length - 2 * chamfer_size}",
            param="screw_hole_width",
        )

    # Channel body: walls either side of a flat-floored slot running the full length.
    body = Pos(body_width / 2, 0, height / 2) * Box(body_width, clip_length, height)
    channel = Pos(body_width / 2, 0, base_thickness + channel_depth) * Box(
        channel_width, clip_length + 2 * chamfer_size, 2 * channel_depth
    )

    # Mounting tab: flush with the bottom, screw hole on the tab's own centre.
    tab_centre_x = body_width + tab_length / 2
    tab = Pos(tab_centre_x, 0, base_thickness / 2) * Box(
        tab_length, clip_length, base_thickness
    )
    screw_hole = Pos(tab_centre_x, 0, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, 2 * base_thickness
    )

    solid = (body + tab) - channel - screw_hole
    if draft:
        return solid

    # Everything the polish pass must not touch: the bed face, the channel it has to
    # keep square, the screw bore, and every concave junction.
    bed = solid.bounding_box().min.Z
    concave = set(concave_edges(solid))

    def keeps_its_corner(edge):
        if edge in concave:
            return False
        box = edge.bounding_box()
        if box.max.Z <= bed + 1e-6:  # lying in the bottom face
            return False
        # Inside the channel: floor, inner wall faces, and the mouth they make.
        if (
            box.min.X >= wall_thickness - 1e-6
            and box.max.X <= wall_thickness + channel_width + 1e-6
            and box.min.Z >= base_thickness - 1e-6
        ):
            return False
        # The screw bore stays a plain cylinder for the head to bear on.
        centre = box.center()
        if abs(centre.X - tab_centre_x) < 1e-6 and abs(centre.Y) < 1e-6:
            return False
        # Skip the top edges running across the part: three chamfers meeting at a
        # corner leave a sliver triangle.
        across = box.max.X - box.min.X > 1e-6
        level = box.max.Z - box.min.Z < 1e-6 and box.max.Y - box.min.Y < 1e-6
        if across and level:
            return False
        return True

    keep = solid.edges().filter_by(keeps_its_corner)
    return polish(solid, keep, chamfer_size)
