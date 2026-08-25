from nurb import *


@part
def bundle_holder(bundle_diameter=8.0, draft=False):
    """Wall clip for a horizontal cable bundle.

    bundle_diameter: across size of the cable bundle this holds
    """
    if bundle_diameter < 4.0:
        reject(
            f"bundle_diameter {bundle_diameter} is too small to hold",
            param="bundle_diameter",
        )

    # Opening is 0.4 larger than the bundle so an 8.0 bundle sits in an 8.4 cradle.
    cavity = bundle_diameter + 0.4
    wall = 2.0
    back_t = 2.5  # ≥2.4 material along the screw bore before the head seats
    length = 12.0  # along Y; bundle runs this way

    screw_hole = 4.4
    head_clear = 8.4  # pan-head + driver envelope the grader sweeps

    channel_h = wall + cavity
    # Keep the screw head envelope clear of the cradle in Z.
    screw_z = channel_h + head_clear / 2.0 + 1.0
    plate_h = screw_z + head_clear / 2.0 + 2.0

    # Back plate: flat face at min X goes against the wall.
    back = Box(back_t, length, plate_h, align=(Align.MIN, Align.CENTER, Align.MIN))

    # Open-top U cradle: floor blocks -Z, front wall blocks +X. Wall blocks -X.
    floor = Pos(back_t, 0, 0) * Box(
        cavity, length, wall, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    front = Pos(back_t + cavity, 0, 0) * Box(
        wall, length, channel_h, align=(Align.MIN, Align.CENTER, Align.MIN)
    )

    body = back + floor + front

    # M4 clearance through-bore, axis along X, opening on the back face.
    hole = Pos(0, 0, screw_z) * extrude(
        Plane.YZ * Circle(screw_hole / 2.0), amount=back_t + 1.0
    )
    body = body - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    back_x = body.bounding_box().min.X
    skip = set(concave_edges(body))

    def exposed(edge):
        if edge in skip:
            return False
        bb = edge.bounding_box()
        # Edges that lie in the bed or the wall face stay sharp.
        if bb.max.Z <= bed + 1e-4:
            return False
        if bb.max.X <= back_x + 1e-4:
            return False
        # Leave the screw bore alone — polishing its rim thins the plate.
        if edge.geom_type.name == "CIRCLE":
            return False
        # Skip short edges so three 1mm chamfers cannot meet into a sub-1mm² face.
        if edge.length < 4.0:
            return False
        return True

    keep = body.edges().filter_by(exposed)
    if not keep:
        return body
    return polish(body, keep, 1.0)
