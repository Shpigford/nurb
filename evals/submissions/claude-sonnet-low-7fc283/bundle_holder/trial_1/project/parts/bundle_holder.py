from nurb import *


@part
def bundle_holder(
    bundle_diameter=8.0,
    bundle_span=12.4,
    wall=2.0,
    screw_shank_dia=4.6,
    screw_head_dia=8.6,
    draft=False,
):
    """
    bundle_diameter: how thick the cable bundle is across
    bundle_span: how far the holder runs along the bundle
    wall: material thickness around the bundle channel and screw bore
    screw_shank_dia: through-bore diameter for the M4 screw shank
    screw_head_dia: clearance diameter for the screw head and driver
    """
    clearance = 0.6
    bore_dia = bundle_diameter + clearance
    bore_r = bore_dia / 2
    screw_head_r = screw_head_dia / 2

    depth_x = wall + bore_dia + wall
    gap = 1.3
    height_z = wall + bore_dia + gap + screw_head_dia + wall

    body = Box(depth_x, bundle_span, height_z)
    body = body.translate((depth_x / 2, bundle_span / 2, height_z / 2))

    bundle_center_z = height_z - wall - bore_r
    screw_center_z = bundle_center_z - bore_r - gap - screw_head_r

    bundle_cyl = Cylinder(bore_r, bundle_span + 4)
    bundle_cyl = bundle_cyl.rotate(Axis.X, 90)
    bundle_cyl = bundle_cyl.translate((wall + bore_r, bundle_span / 2, bundle_center_z))
    body = body - bundle_cyl

    shank_len = 2.8
    shank = Cylinder(screw_shank_dia / 2, shank_len)
    shank = shank.rotate(Axis.Y, 90)
    shank = shank.translate((shank_len / 2, bundle_span / 2, screw_center_z))

    head_len = depth_x - shank_len + 1.0
    head = Cylinder(screw_head_r, head_len)
    head = head.rotate(Axis.Y, 90)
    head = head.translate((shank_len + head_len / 2, bundle_span / 2, screw_center_z))

    body = body - shank - head

    if draft:
        return body

    bed = body.bounding_box().min.Z
    back = body.bounding_box().min.X
    concave = concave_edges(body)

    tol = 1e-4

    def keep_edge(e):
        bb = e.bounding_box()
        if bb.min.Z <= bed + tol:
            return False
        if bb.max.X <= back + tol:
            return False
        return True

    keep = body.edges().filter_by(keep_edge) - concave
    return polish(body, keep, 1.0)
