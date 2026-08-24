from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), holder_length=12.0, draft=False):
    """A wall clip that cradles a horizontal cable bundle, held by one M4 screw above it.

    bundle_diameter: how thick the cable bundle is across
    holder_length: how far the clip runs along the bundle
    """
    if bundle_diameter < 3.0:
        reject(
            "bundle_diameter under 3 leaves a channel too small to print or thread: use 3.0 or more",
            param="bundle_diameter",
        )
    if holder_length < 10.0:
        reject(
            "holder_length under 10 gives less wall grip than the mount needs: use 10.0 or more",
            param="holder_length",
        )

    back_t = 3.0                              # material along the screw bore before the head seats
    floor_t = 2.0                             # channel floor, blocks the bundle downward
    lip_t = 3.0                               # front lip, blocks the bundle away from the wall
    channel = bundle_diameter + 0.6           # 0.3 of clearance each side of the bundle
    bundle_z = floor_t + bundle_diameter / 2.0 + 0.5
    lip_top = bundle_z + 2.0
    head_r = 4.2                              # M4 pan head and driver, ISO plus clearance
    # High enough that the driver clears the lip and the seated head clears the bundle.
    screw_z = max(lip_top + head_r + 1.0, bundle_z + bundle_diameter / 2.0 + head_r)
    # Head seat stays solid to the head's rim even after the 1.25 top chamfer.
    height = screw_z + head_r + 1.75
    y_mid = holder_length / 2.0

    body = Pos(back_t / 2.0, y_mid, height / 2.0) * Box(back_t, holder_length, height)
    body += Pos(back_t + channel / 2.0, y_mid, floor_t / 2.0) * Box(channel, holder_length, floor_t)
    body += Pos(back_t + channel + lip_t / 2.0, y_mid, lip_top / 2.0) * Box(lip_t, holder_length, lip_top)

    # M4 clearance bore, medium fit, axis along X, opening on the back face.
    bore = Pos(back_t / 2.0, y_mid, screw_z) * Rot(0, 90, 0) * Cylinder(2.25, back_t + 2.0)
    body -= bore

    if draft:
        return body

    eps = 1e-6
    concave = concave_edges(body)

    def keepable(e):
        bb = e.bounding_box()
        if bb.max.X < eps:          # lies in the back face, stays sharp against the wall
            return False
        if bb.max.Z < eps:          # lies in the bed face
            return False
        c = e.center()
        if ((c.Y - y_mid) ** 2 + (c.Z - screw_z) ** 2) ** 0.5 < 3.0:
            return False            # bore mouth: the head seat stays full
        return e not in concave

    keep = body.edges().filter_by(keepable)
    # 1.25 rather than 1.0: the corner triangle three chamfers leave stays over
    # the 1mm2 sliver floor, so the part carries no sub-millimetre faces at all.
    return polish(body, keep, 1.25)
