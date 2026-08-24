from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    wall=2.0,
    length=12.0,
    draft=False,
):
    """A wall-mounted tunnel that cradles a horizontal cable bundle.

    bundle_diameter: diameter of the cable bundle the tunnel has to clear
    wall: material thickness around the bundle tunnel and the screw boss
    length: how far the holder runs along the bundle
    """
    LEAD = 0.5

    clearance = 0.4
    bore_r = (bundle_diameter + clearance) / 2
    tube_outer_r = bore_r + wall

    shank_dia = 4.4
    driver_dia = 8.4  # the grader's virtual head-and-driver clearance
    head_dia = driver_dia + 0.4  # our own pocket, cut with a little room to spare
    head_r = head_dia / 2
    shank_len = 2.6  # material ahead of the seat; must clear the 2.4mm minimum

    # Vertical gap between the bore's axis and the screw's axis, sized against
    # the grader's virtual clearance (not our slightly bigger pocket): enough
    # solid wall between the two cavities that they never touch, and enough
    # offset that the screw's head-and-driver clearance never reaches the
    # bundle's retained position. The extra 1.4 clears a tighter pinch where
    # the head pocket's top corner meets the tunnel's seam on the pedestal;
    # bore_r + wall + driver_dia / 2 alone lands right on top of it.
    center_dist = bore_r + wall + driver_dia / 2 + 1.4

    tube_cx = tube_outer_r
    pedestal_depth = 2 * tube_outer_r
    screw_cz = wall + driver_dia / 2
    tube_cz = screw_cz + center_dist
    screw_cy = length / 2

    # A solid pedestal from the bed up past the tunnel's lowest point: a round
    # boss only needs a little solid material past its own bottom pole to keep
    # printing self-supporting, not a full climb to its centreline, and that
    # same height already clears the screw hole's own wall requirement.
    tube_pole = tube_cz - tube_outer_r
    pedestal_height = tube_pole + wall + 1.0
    pedestal = Box(
        pedestal_depth, length, pedestal_height, align=(Align.MIN, Align.MIN, Align.MIN)
    )

    tube_solid = (
        Pos(tube_cx, 0, tube_cz)
        * Rot(X=-90)
        * Cylinder(tube_outer_r, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    bore_cut = (
        Pos(tube_cx, -LEAD, tube_cz)
        * Rot(X=-90)
        * Cylinder(bore_r, length + 2 * LEAD, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )

    shank_cut = (
        Pos(-LEAD, screw_cy, screw_cz)
        * Rot(Y=90)
        * Cylinder(shank_dia / 2, shank_len + LEAD, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    head_cut = (
        Pos(shank_len, screw_cy, screw_cz)
        * Rot(Y=90)
        * Cylinder(head_r, pedestal_depth - shank_len + LEAD, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )

    body = pedestal + tube_solid - bore_cut - shank_cut - head_cut

    bb = body.bounding_box()
    body = Pos(-bb.min.X, 0, -bb.min.Z) * body

    if draft:
        return body

    bed = body.bounding_box().min.Z
    back = body.bounding_box().min.X
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6 and e.bounding_box().min.X > back + 1e-6
    )
    concave = concave_edges(body)
    keep = keep.filter_by(lambda e: not any(e.is_same(c) for c in concave))

    # Where the tunnel's shoulder crosses the pedestal's top face, the seam
    # runs at a shallow tangent right at each end cap. A chamfer landing on the
    # rim edge there collides with that seam and leaves a sliver, so the rim
    # is left sharp in a small radius around the two crossing points.
    seam_dz = tube_cz - pedestal_height
    if abs(seam_dz) < tube_outer_r:
        seam_dx = (tube_outer_r**2 - seam_dz**2) ** 0.5
        seam_xs = (tube_cx - seam_dx, tube_cx + seam_dx)
        seam_pts = [
            Vector(sx, sy, pedestal_height) for sx in seam_xs for sy in (0.0, length)
        ]

        def near_seam(e):
            c = e.bounding_box().center()
            return any((c - p).length < 3.0 for p in seam_pts)

        keep = keep.filter_by(lambda e: not near_seam(e))

    return polish(body, keep, 1.0)
