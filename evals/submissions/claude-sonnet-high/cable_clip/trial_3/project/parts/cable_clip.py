from nurb import *


@part
def cable_clip(
    bundle_diameter=measured("bundle_diameter"),
    channel_clearance=0.4,
    wall_thickness=2.4,
    base_thickness=3.0,
    clip_length=12.0,
    tab_length=10.0,
    mounting_hole_diameter=4.2,
    draft=False,
):
    """
    bundle_diameter: how thick the cable bundle is, across
    channel_clearance: extra room in the channel beyond the bundle's own thickness
    wall_thickness: how thick the two channel walls are
    base_thickness: how thick the solid base under the channel is
    clip_length: how long the clip runs along the cable
    tab_length: how far the mounting tab sticks out past the wall
    mounting_hole_diameter: the screw's through-hole diameter in the tab
    """
    channel_width = bundle_diameter + channel_clearance
    channel_depth = bundle_diameter
    total_height = base_thickness + channel_depth
    total_width = tab_length + 2 * wall_thickness + channel_width

    channel_x_min = tab_length + wall_thickness
    channel_x_max = channel_x_min + channel_width

    base = Pos(0, 0, 0) * Box(
        total_width, clip_length, base_thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    left_wall = Pos(tab_length, 0, base_thickness) * Box(
        wall_thickness, clip_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    right_wall = Pos(channel_x_max, 0, base_thickness) * Box(
        wall_thickness, clip_length, channel_depth,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    hole = Pos(tab_length / 2, clip_length / 2, -1.0) * Cylinder(
        mounting_hole_diameter / 2, base_thickness + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    body = base + left_wall + right_wall - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))

    def exposed(e):
        bb = e.bounding_box()
        if bb.min.Z <= bed + 1e-6:
            return False
        # the channel is fit-critical mating geometry: never polish it, floor included
        if bb.max.X > channel_x_min - 1e-6 and bb.min.X < channel_x_max + 1e-6 and bb.max.Z > base_thickness - 1e-6:
            return False
        # the screw hole's rim is functional fit geometry: never polish it
        if e.geom_type.name == "CIRCLE":
            return False
        return True

    keep = [e for e in body.edges().filter_by(exposed) if e not in concave]
    return polish(body, keep, 1.0)
