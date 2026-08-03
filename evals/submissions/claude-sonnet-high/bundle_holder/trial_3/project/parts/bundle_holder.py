from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    channel_clearance=0.5,
    wall=1.3,
    screw_shank_dia=4.4,
    screw_land=2.5,
    screw_head_dia=8.5,
    screw_head_clear=3.6,
    length=13.0,
    draft=False,
):
    """
    bundle_diameter: diameter of the cable bundle the channel must hold
    channel_clearance: extra room added to the bundle diameter so it slides through
    wall: material thickness kept around every bore
    screw_shank_dia: through-bore diameter for the M4 screw shank
    screw_land: solid material the shank passes through before the head seats
    screw_head_dia: diameter of the head-and-driver clearance bore
    screw_head_clear: depth of the head clearance bore, from the seat to the front face
    length: how far the holder runs along the cable bundle
    """
    channel_dia = bundle_diameter + channel_clearance
    channel_r = channel_dia / 2.0

    # Tube zone: wraps the bundle channel with `wall` all around, grounded on the bed.
    x_tube = 2 * wall + channel_dia
    z_tube_c = wall + channel_r
    channel_top = z_tube_c + channel_r

    # Screw zone stacks above, then steps inward (shallower) so the whole profile stays
    # self-supporting as it rises. The step sits `wall` above the channel bore and
    # `wall` below the screw bore, since the tube zone's shoulder is unsupported past
    # the screw zone's footprint and needs its own clearance to the channel below it.
    step_z = channel_top + wall
    screw_bottom = step_z + wall
    z_screw_c = screw_bottom + screw_head_dia / 2.0
    h_total = z_screw_c + screw_head_dia / 2.0 + wall

    tube_h = step_z
    screw_h = h_total - step_z

    x_screw = screw_land + screw_head_clear

    length = max(length, screw_head_dia + 2 * wall)

    tube_zone = Pos(x_tube / 2.0, length / 2.0, tube_h / 2.0) * Box(x_tube, length, tube_h)
    screw_zone = Pos(x_screw / 2.0, length / 2.0, step_z + screw_h / 2.0) * Box(x_screw, length, screw_h)
    body = tube_zone + screw_zone

    channel_bore = Pos(wall + channel_r, length / 2.0, z_tube_c) * Rot(X=90) * Cylinder(
        radius=channel_r, height=length + 2.0
    )

    # Cylinder() is centered on its own axis, so each bore is placed by its midpoint,
    # not its start; overlap the shank and head bores across the seat so their union
    # has no gap.
    shank_start, shank_end = -1.0, screw_land + 0.5
    shank_bore = Pos(
        (shank_start + shank_end) / 2.0, length / 2.0, z_screw_c
    ) * Rot(Y=90) * Cylinder(radius=screw_shank_dia / 2.0, height=shank_end - shank_start)

    head_start, head_end = screw_land - 0.5, x_screw + 1.0
    head_bore = Pos(
        (head_start + head_end) / 2.0, length / 2.0, z_screw_c
    ) * Rot(Y=90) * Cylinder(radius=screw_head_dia / 2.0, height=head_end - head_start)

    body = body - channel_bore - shank_bore - head_bore

    if draft:
        return body

    bed = body.bounding_box().min.Z
    back = body.bounding_box().min.X
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
        and e.bounding_box().min.X > back + 1e-6
        and e not in concave
    )
    return polish(body, keep, 1.0)
