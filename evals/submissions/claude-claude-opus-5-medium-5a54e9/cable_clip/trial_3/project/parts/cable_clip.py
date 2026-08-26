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
    """A screw-down clip that pins a cable bundle to a flat surface.

    bundle_diameter: how thick the cable bundle is across
    cable_clearance: extra width in the channel so the bundle drops in
    wall_thickness: how thick each channel wall is
    base_thickness: how much material sits under the cable, and how thick the tab is
    clip_length: how far the clip runs along the cable
    tab_length: how far the screw tab sticks out sideways
    screw_hole_width: the through-hole for the mounting screw
    """
    if bundle_diameter < 2.0:
        reject(
            f"bundle_diameter {bundle_diameter} leaves a channel too narrow to print or "
            "load: raise it above 2.0",
            param="bundle_diameter",
        )

    channel_width = bundle_diameter + cable_clearance
    channel_depth = bundle_diameter
    body_width = 2 * wall_thickness + channel_width
    total_height = base_thickness + channel_depth
    channel_x0 = wall_thickness
    channel_x1 = wall_thickness + channel_width
    hole_x = body_width + tab_length / 2

    body = Pos(body_width / 2, 0, total_height / 2) * Box(
        body_width, clip_length, total_height
    )
    tab = Pos(hole_x, 0, base_thickness / 2) * Box(
        tab_length, clip_length, base_thickness
    )
    # Open-topped and open-ended: overshoot in +Z and in Y so no coincident faces survive.
    channel = Pos(
        channel_x0 + channel_width / 2, 0, base_thickness + channel_depth
    ) * Box(channel_width, clip_length + 2.0, 2 * channel_depth)
    hole = Pos(hole_x, 0, base_thickness / 2) * Cylinder(
        screw_hole_width / 2, base_thickness + 2.0
    )

    solid = body + tab - channel - hole
    if draft:
        return solid

    # Nothing inside the channel is touched: the floor stays one flat face the full
    # channel width, and the mouth gets no lead-in. Nothing lying in the bed face is
    # touched either, and concave junctions are never chamfered. The screw hole's rim
    # is left sharp as well: a cone on a 3mm tab necks the section under it.
    eps = 1e-6
    concave = [e.center() for e in concave_edges(solid)]

    def inside_channel(e):
        bb = e.bounding_box()
        return (
            bb.min.X > channel_x0 - eps
            and bb.max.X < channel_x1 + eps
            and bb.min.Z > base_thickness - eps
        )

    def in_bed_face(e):
        return e.bounding_box().max.Z < eps

    def is_screw_hole(e):
        return e.geom_type.name == "CIRCLE"

    def is_concave(e):
        c = e.center()
        return any((c - p).length < eps for p in concave)

    keep = solid.edges().filter_by(
        lambda e: not inside_channel(e)
        and not in_bed_face(e)
        and not is_screw_hole(e)
        and not is_concave(e)
    )
    # 1.2 rather than the family's 1.0: the corner triangle three chamfers leave is
    # 0.866 * size**2, and at 1.0 that is 0.87mm2, under this printer's 1mm2 sliver
    # floor. 1.2 puts it at 1.25mm2 and every face on the part is a face you can print.
    return polish(solid, keep, 1.2)
