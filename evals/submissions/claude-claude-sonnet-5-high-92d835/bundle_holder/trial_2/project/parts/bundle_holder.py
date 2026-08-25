from nurb import *


@part
def bundle_holder(
    bundle_diameter=8.0,
    length=16.0,
    wall=1.5,
    clearance=0.5,
    screw_shank=4.4,
    screw_head=8.4,
    shank_len=2.6,
    head_len=3.6,
    draft=False,
):
    """A wall-mounted clip: a closed tunnel threads the cable bundle along Y, and a
    boss above it takes one M4 pan-head screw straight into the wall along X.

    bundle_diameter: how thick the cable bundle is, measured across the taped bundle
    length: how far the holder runs along the bundle
    wall: material thickness around the tunnel and the screw boss
    clearance: how much roomier the tunnel is than the bundle, so it threads through
    screw_shank: the through-bore for the screw's shank, opening on the back face
    screw_head: the bore cleared for the pan head and driver, in front of the shank
    shank_len: how much wall the shank passes through before the head seats
    head_len: how deep the head's pocket reaches before it opens to the front face
    """
    if bundle_diameter <= 0:
        reject("bundle_diameter must be positive", param="bundle_diameter")
    if shank_len < 2.4:
        reject("shank_len needs at least 2.4mm of material before the head seats", param="shank_len")
    if screw_head <= screw_shank:
        reject("screw_head must be wider than screw_shank", param="screw_head")

    channel_dia = bundle_diameter + clearance
    channel_r = channel_dia / 2
    tunnel = channel_dia + 2 * wall  # square cross-section wrapping the tunnel
    x_c = z_c = tunnel / 2

    screw_r = screw_head / 2
    z_s = tunnel + wall + screw_r  # a full wall of separation above the tunnel roof
    boss_half = screw_r + wall
    boss_top = z_s + screw_r + wall

    # The boss shares the tunnel's own depth, front face flush with it: no ledge in
    # front of the boss for a concave step to hide a thin diagonal measurement in.
    depth_boss = tunnel
    if depth_boss < shank_len + head_len:
        reject(
            f"bundle_diameter {bundle_diameter:g} makes the tunnel only {depth_boss:.1f}mm "
            f"deep, under the {shank_len + head_len:.1f}mm the screw bore needs; raise "
            "bundle_diameter or shrink shank_len/head_len",
            param="bundle_diameter",
        )

    min_length = 2 * (boss_half + wall)
    floor_length = max(10.0, min_length)
    if length < floor_length:
        reject(
            f"length {length:g} is under the {floor_length:g}mm the screw boss and "
            "its side walls need",
            param="length",
        )
    y_s = length / 2

    tunnel_block = Box(tunnel, length, tunnel, align=(Align.MIN, Align.MIN, Align.MIN))
    boss_block = Pos(0, y_s, 0) * Box(
        depth_boss, 2 * boss_half, boss_top, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    body = tunnel_block + boss_block

    channel_hole = Pos(x_c, 0, z_c) * Cylinder(
        channel_r, length, rotation=(-90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    shank_hole = Pos(0, y_s, z_s) * Cylinder(
        screw_shank / 2, shank_len, rotation=(0, 90, 0), align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    head_hole = Pos(shank_len, y_s, z_s) * Cylinder(
        screw_r, depth_boss - shank_len, rotation=(0, 90, 0), align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    body = body - channel_hole - shank_hole - head_hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    back = body.bounding_box().min.X
    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: not (
            abs(e.bounding_box().min.Z - bed) < 1e-6 and abs(e.bounding_box().max.Z - bed) < 1e-6
        )
        and not (
            abs(e.bounding_box().min.X - back) < 1e-6 and abs(e.bounding_box().max.X - back) < 1e-6
        )
    )
    keep = [e for e in keep if e not in concave]
    return polish(body, keep, 1.0)
