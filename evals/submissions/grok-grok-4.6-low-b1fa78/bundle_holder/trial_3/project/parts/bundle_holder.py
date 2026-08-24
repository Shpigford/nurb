from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    draft=False,
):
    """Wall clip for a taped cable bundle, one M4 pan-head screw.

    bundle_diameter: measured width of the cable bundle
    """
    inner = bundle_diameter + 0.4
    wall = 2.0
    back_t = 2.8
    length = 14.0
    floor_t = 2.0
    lip_t = 2.0
    screw_d = 4.4
    head_clear = 8.4
    around = 2.4

    pocket_top = floor_t + inner
    screw_z = pocket_top + head_clear / 2.0 + 1.6
    back_h = screw_z + screw_d / 2.0 + around

    back = Box(back_t, length, back_h).moved(Location((back_t / 2.0, 0.0, back_h / 2.0)))
    floor = Box(back_t + inner + lip_t, length, floor_t).moved(
        Location(((back_t + inner + lip_t) / 2.0, 0.0, floor_t / 2.0))
    )
    lip = Box(lip_t, length, pocket_top).moved(
        Location((back_t + inner + lip_t / 2.0, 0.0, pocket_top / 2.0))
    )
    body = back + floor + lip

    hole = Cylinder(screw_d / 2.0, back_t + 2.0).moved(
        Location((back_t / 2.0, 0.0, screw_z), (0.0, 90.0, 0.0))
    )
    body = body - hole

    if draft:
        return body
    bed = body.bounding_box().min.Z
    hole_z0 = screw_z - screw_d / 2.0 - 1.2
    hole_z1 = screw_z + screw_d / 2.0 + 1.2
    inner_x0 = back_t - 0.2
    inner_x1 = back_t + inner + 0.2

    def polishable(e):
        bb = e.bounding_box()
        if bb.min.Z <= bed + 0.05:
            return False
        if e.length < 8.0:
            return False
        mx = (bb.min.X + bb.max.X) / 2.0
        mz = (bb.min.Z + bb.max.Z) / 2.0
        if hole_z0 <= mz <= hole_z1 and mx < back_t + 1.0:
            return False
        if inner_x0 <= mx <= inner_x1 and mz < pocket_top + 0.5:
            return False
        return True

    keep = body.edges().filter_by(polishable)
    return polish(body, keep, 1.0)
