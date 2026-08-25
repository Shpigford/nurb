from nurb import *


@part
def bundle_holder(
    bundle_diameter=8.0,
    length=13.2,
    wall=2.0,
    channel_clearance=0.5,
    screw_shank_hole=4.5,
    screw_head_clearance=8.7,
    screw_seat_length=3.0,
    draft=False,
):
    """Wall-mounted hook that cradles a horizontal cable bundle, screwed to the wall with one M4.

    bundle_diameter: the cable bundle's own diameter, measured across the taped bundle
    length: how far the holder runs along the bundle
    wall: material thickness around the cable channel and the screw boss
    channel_clearance: extra diameter left around the bundle so it slides in freely
    screw_shank_hole: clearance bore for the M4 shank, from the wall to where the head seats
    screw_head_clearance: clearance bore for the M4 pan head and a driver bit
    screw_seat_length: how far in from the wall the shank hole runs before the head seats
    """
    if channel_clearance < 0.4:
        reject(
            f"channel_clearance {channel_clearance:g} is under the 0.4mm the bundle "
            "needs to actually slide in, raise it above 0.4",
            param="channel_clearance",
        )
    if screw_seat_length < 2.4:
        reject(
            f"screw_seat_length {screw_seat_length:g} is under the 2.4mm of material "
            "the M4 head needs before it seats, raise it above 2.4",
            param="screw_seat_length",
        )
    if screw_head_clearance <= screw_shank_hole:
        reject(
            f"screw_head_clearance {screw_head_clearance:g} needs to clear the M4 head "
            f"and driver, wider than screw_shank_hole {screw_shank_hole:g}",
            param="screw_head_clearance",
        )

    channel_dia = bundle_diameter + channel_clearance
    r_c = channel_dia / 2.0
    r_out = r_c + wall
    depth = 2 * r_out
    x_c = r_out

    min_length = screw_head_clearance + 2 * wall
    if length < max(min_length, 10.0):
        reject(
            f"length {length:g} is under {max(min_length, 10.0):g}mm: the screw boss "
            f"needs {wall:g}mm of wall on each side of its {screw_head_clearance:g}mm bore",
            param="length",
        )

    # The hook wraps the channel from the back, under the bottom, and up the front to
    # about the bundle's equator, left open at the top so the cable drops in from above.
    top_z = 0.4 * r_c
    collar_bottom_z = -(r_c + wall)
    boss_h = screw_head_clearance + 2 * wall
    bottom_z = collar_bottom_z - boss_h
    height = top_z - bottom_z

    block = Pos(0, 0, bottom_z) * Box(
        depth, length, height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    channel_cut = Pos(x_c, -1, 0) * Rot(X=-90) * Cylinder(
        r_c, length + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )

    z_bore = collar_bottom_z - boss_h / 2.0
    y_bore = length / 2.0

    shank_cut = Pos(-1, y_bore, z_bore) * Rot(Y=90) * Cylinder(
        screw_shank_hole / 2.0,
        screw_seat_length + 1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    head_cut = Pos(screw_seat_length, y_bore, z_bore) * Rot(Y=90) * Cylinder(
        screw_head_clearance / 2.0,
        depth - screw_seat_length + 1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    body = block - channel_cut - shank_cut - head_cut

    if draft:
        return body

    bb = body.bounding_box()
    back_x = bb.min.X
    bed_z = bb.min.Z

    faces = body.faces()
    back_faces = faces.filter_by(
        lambda f: f.bounding_box().max.X - f.bounding_box().min.X < 1e-6
        and abs(f.bounding_box().min.X - back_x) < 1e-6
    )
    bottom_faces = faces.filter_by(
        lambda f: f.bounding_box().max.Z - f.bounding_box().min.Z < 1e-6
        and abs(f.bounding_box().min.Z - bed_z) < 1e-6
    )

    def on_channel(e):
        c = e.center()
        r = ((c.X - x_c) ** 2 + c.Z ** 2) ** 0.5
        return abs(r - r_c) < 0.05

    channel_edges = body.edges().filter_by(on_channel)

    end_faces = faces.filter_by(
        lambda f: f.bounding_box().max.Y - f.bounding_box().min.Y < 1e-6
    )

    skip = (
        set(back_faces.edges())
        | set(bottom_faces.edges())
        | set(concave_edges(body))
        | set(channel_edges)
        | set(end_faces.edges())
    )
    keep = body.edges().filter_by(lambda e: e not in skip)

    return polish(body, keep, 1.0)
