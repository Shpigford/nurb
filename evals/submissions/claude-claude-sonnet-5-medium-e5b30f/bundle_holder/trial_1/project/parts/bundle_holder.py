import math

from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, length=14.0, wall_thickness=1.2, draft=False):
    """
    bundle_diameter: how thick the cable bundle is across
    length: how long the holder runs along the bundle
    wall_thickness: how thick the material is around the bundle channel and screw bore
    """
    clearance = 0.5
    channel_r = (bundle_diameter + clearance) / 2
    tube_outer_r = channel_r + wall_thickness

    back_t = 2.4
    # tall enough for 100mm2 of back-face area, and clear of the tube's dome by
    # a real margin (not a hair) so the two don't leave a sliver where they meet
    back_h = max(6.0, 100.0 / length + 0.4, tube_outer_r + 4.0)

    screw_shank_r = 4.4 / 2
    screw_head_r = 8.4 / 2
    seat_x = back_t + 0.3
    head_depth = 4.0
    boss_x_max = seat_x + head_depth

    screw_w = screw_head_r + wall_thickness

    x_t = tube_outer_r
    z_t = tube_outer_r
    tube_top = 2 * tube_outer_r

    # the screw boss sits clear above the tube; a 45deg wedge widens the thin
    # riser out to the boss's full depth so nothing droops past 45deg getting there
    taper_h = boss_x_max - back_t
    riser_top = tube_top + taper_h

    z_s = riser_top + screw_head_r + wall_thickness
    col_top = z_s + screw_head_r + wall_thickness + 1.0
    y_s = length / 2

    # tube, flattened at the bottom so its outer surface never droops past 45deg;
    # cut a bit past the 45deg line so mesh tessellation at the seam can't tip it over
    corbel_angle = 65
    tube = Pos(x_t, length / 2, z_t) * Rot(X=-90) * Cylinder(tube_outer_r, length)
    corbel_half_w = tube_outer_r * math.sin(math.radians(corbel_angle))
    corbel_h = tube_outer_r * (1 - math.cos(math.radians(corbel_angle)))
    tube_foot = Pos(x_t, length / 2, corbel_h / 2) * Box(
        2 * corbel_half_w, length, corbel_h
    )
    tube = tube + tube_foot

    back_plate = Pos(back_t / 2, length / 2, back_h / 2) * Box(back_t, length, back_h)

    riser = Pos(back_t / 2, y_s, riser_top / 2) * Box(back_t, 2 * screw_w, riser_top)

    wedge_profile = Plane.XZ * make_face(
        Polyline(
            [
                (back_t, tube_top),
                (boss_x_max, riser_top),
                (back_t, riser_top),
            ],
            close=True,
        )
    )
    wedge = Pos(0, y_s + screw_w, 0) * extrude(wedge_profile, amount=2 * screw_w)

    screw_col = Pos(
        boss_x_max / 2, y_s, riser_top + (col_top - riser_top) / 2
    ) * Box(boss_x_max, 2 * screw_w, col_top - riser_top)

    body = back_plate + tube + riser + wedge + screw_col

    channel_cut = (
        Pos(x_t, length / 2, z_t)
        * Rot(X=-90)
        * Cylinder(channel_r, length + 1.0)
    )
    shank_cut = (
        Pos(seat_x / 2 - 0.25, y_s, z_s)
        * Rot(Y=90)
        * Cylinder(screw_shank_r, seat_x + 0.5)
    )
    head_cut = (
        Pos((boss_x_max + seat_x) / 2, y_s, z_s)
        * Rot(Y=90)
        * Cylinder(screw_head_r, boss_x_max - seat_x + 0.5)
    )

    body = body - channel_cut - shank_cut - head_cut

    if draft:
        return body

    bb = body.bounding_box()
    bed = bb.min.Z
    back = bb.min.X
    y_min = bb.min.Y
    y_max = bb.max.Y
    tol = 1e-6

    def lies_flat(e, axis, value):
        ebb = e.bounding_box()
        lo = getattr(ebb.min, axis)
        hi = getattr(ebb.max, axis)
        return abs(lo - value) < tol and abs(hi - value) < tol

    # the tube's own end rims are excluded too: chamfering that curved edge
    # right where it crests near the top droops well past the 45deg limit
    #
    # the corbel foot meets the tube exactly on its 45deg limit; chamfering
    # that tangent seam pushes the exposed cylinder past 45deg, so it stays sharp
    keep = body.edges().filter_by(
        lambda e: not lies_flat(e, "Z", bed)
        and not lies_flat(e, "X", back)
        and not lies_flat(e, "Z", corbel_h)
        and not lies_flat(e, "Z", tube_top)
        and not lies_flat(e, "Z", back_h)
        and not lies_flat(e, "X", back_t)
        and not (lies_flat(e, "Y", y_min) and e.geom_type.name == "CIRCLE")
        and not (lies_flat(e, "Y", y_max) and e.geom_type.name == "CIRCLE")
    ) - concave_edges(body)
    return polish(body, keep, 1.0)
