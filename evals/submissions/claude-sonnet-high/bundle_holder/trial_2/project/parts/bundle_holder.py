from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    wall_thickness=2.0,
    holder_length=10.0,
    draft=False,
):
    """
    bundle_diameter: the cable bundle's outside diameter
    wall_thickness: material around the cable channel and the screw boss
    holder_length: how far the holder runs along the cable bundle
    """
    # M4 pan-head screw: 4.0 shank, 8.4 head-and-driver clearance.
    screw_shank_r = 2.2
    screw_head_clear_r = 4.2
    seat_depth = 2.55          # material ahead of the screw head before it seats (>= 2.4)
    head_room = 3.8            # counterbore depth past the seat (screw head stands 3.2 tall)
    head_bore_r = screw_head_clear_r + 0.15
    boss_half = head_bore_r + wall_thickness

    bundle_clear = (bundle_diameter + 0.4) / 2.0 + 0.04
    tube_r = bundle_clear + wall_thickness

    # Keep the bundle and the installed screw apart: separate their axes in Z
    # by more than the sum of their clearance radii, so the two never overlap.
    channel_gap = bundle_clear + head_bore_r + 0.4

    spine_t = wall_thickness
    boss_len = 2 * boss_half
    length = max(holder_length, boss_len + 1.0)

    z_screw = 0.0
    z_bundle = z_screw + channel_gap
    tube_cx = tube_r  # tube's back wall (bore to back face) == wall_thickness

    top = z_bundle + tube_r
    bottom = z_screw - boss_half
    height = top - bottom
    z_mid = (top + bottom) / 2.0

    spine = Pos(spine_t / 2, length / 2, z_mid) * Box(spine_t, length, height)
    tube = Pos(tube_cx, length / 2, z_bundle) * (Rot(X=90) * Cylinder(tube_r, length))

    boss_front = seat_depth + head_room
    boss = Pos(boss_front / 2, length / 2, z_screw) * Box(boss_front, boss_len, 2 * boss_half)

    body = spine + tube + boss

    bundle_bore = Pos(tube_cx, length / 2, z_bundle) * (
        Rot(X=90) * Cylinder(bundle_clear, length + 4)
    )
    shank_bore = Pos((seat_depth - 2) / 2, length / 2, z_screw) * (
        Rot(Y=90) * Cylinder(screw_shank_r, seat_depth + 2)
    )
    head_end = boss_front + 1
    head_bore = Pos((seat_depth + head_end) / 2, length / 2, z_screw) * (
        Rot(Y=90) * Cylinder(head_bore_r, head_end - seat_depth)
    )

    body = body - bundle_bore - shank_bore - head_bore

    if draft:
        return body

    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e not in concave
        and not (abs(e.bounding_box().min.X) < 1e-6 and abs(e.bounding_box().max.X) < 1e-6)
    )
    return polish(body, keep, 1.0)
