from nurb import *

LEAD = 1.0
HEAD_HEIGHT = 3.2  # M4 pan head height


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    clearance=0.4,
    wall_thickness=1.8,
    screw_shank_hole=4.5,
    screw_head_hole=8.45,
    screw_seat_depth=2.6,
    draft=False,
):
    """A wall-mounted corner cradle for a horizontal cable bundle, screwed to the
    wall with one M4 pan-head screw.

    bundle_diameter: the cable bundle's outside diameter, the cradle is sized around it
    clearance: extra room in the cradle so the bundle slides through freely
    wall_thickness: material thickness around the screw bore and the cradle's floor/wall
    screw_shank_hole: clearance hole diameter for the M4 screw's shank
    screw_head_hole: clearance diameter for the M4 pan head and a driver bit
    screw_seat_depth: material between the wall and where the screw head seats
    """
    bore_r = (bundle_diameter + clearance) / 2

    # The screw boss: a flat-faced block standing on the bed and against the wall,
    # sized around the stepped screw bore. Its footprint (Y and Z) is square so the
    # bore keeps equal wall_thickness cover on every side.
    footprint = screw_head_hole + 2 * wall_thickness
    holder_length = footprint

    # The cradle above it is an L: a floor the bundle rests on, and a front wall that
    # stops it sliding away from the wall, meeting the bundle at its two tangent points.
    floor_depth = 2 * bore_r
    cradle_depth = floor_depth + wall_thickness
    cradle_height = 2 * wall_thickness + 2 * bore_r

    # The screw boss must reach at least as deep as the cradle above it, or the
    # cradle would overhang past the boss's front face with nothing underneath.
    screw_reach = screw_seat_depth + HEAD_HEIGHT + wall_thickness
    depth = max(cradle_depth, screw_reach)

    screw_boss = Box(depth, holder_length, footprint, align=(Align.MIN, Align.MIN, Align.MIN))

    z_floor = footprint
    cradle_block = Pos(0, 0, z_floor) * Box(
        depth, holder_length, cradle_height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    notch = Pos(0, 0, z_floor + wall_thickness) * Box(
        floor_depth, holder_length, cradle_height - wall_thickness, align=(Align.MIN, Align.MIN, Align.MIN)
    )

    z_screw = footprint / 2
    y_screw = holder_length / 2

    shank_x0, shank_x1 = -LEAD, screw_seat_depth
    shank_hole = Pos((shank_x0 + shank_x1) / 2, y_screw, z_screw) * (
        Rot(0, 90, 0)
        * Cylinder(
            screw_shank_hole / 2,
            shank_x1 - shank_x0,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
    )
    head_x0, head_x1 = screw_seat_depth, depth + LEAD
    head_hole = Pos((head_x0 + head_x1) / 2, y_screw, z_screw) * (
        Rot(0, 90, 0)
        * Cylinder(
            screw_head_hole / 2,
            head_x1 - head_x0,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
    )

    body = screw_boss + cradle_block - notch - shank_hole - head_hole

    if draft:
        return body

    back = body.faces().filter_by(lambda f: abs(f.center().X) < 1e-6)
    bottom = body.faces().filter_by(lambda f: abs(f.center().Z) < 1e-6)
    skip_faces = back + bottom
    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: not any(e in f.edges() for f in skip_faces) and e not in concave
    )
    return polish(body, keep, 1.1)
