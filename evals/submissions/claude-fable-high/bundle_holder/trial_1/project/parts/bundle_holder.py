from math import sqrt

from nurb import *


@part
def bundle_holder(
    bundle_diameter=measured("bundle_diameter"),
    holder_length=12.0,
    draft=False,
):
    """Wall clip for a horizontal cable bundle, one M4 screw above the cradle.

    bundle_diameter: how thick the cable bundle is across
    holder_length: how long the clip runs along the bundle
    """
    fit_gap = 0.6      # side room in the channel so the bundle threads through
    back_wall = 2.6    # what the screw clamps; an M4 head needs 2.4 of thread run
    floor_wall = 2.0
    lip_wall = 2.4
    screw_hole = 4.4
    head_dia = 8.4     # M4 pan head plus driver clearance

    channel = bundle_diameter + fit_gap
    front = back_wall + channel + lip_wall
    lip_top = floor_wall + bundle_diameter / 2 + 1.0
    screw_z = floor_wall + bundle_diameter + head_dia / 2 + 1.0
    top = screw_z + head_dia / 2 + 1.5
    length = holder_length

    body = Pos(back_wall / 2, length / 2, top / 2) * Box(back_wall, length, top)
    body += Pos(front / 2, length / 2, floor_wall / 2) * Box(front, length, floor_wall)
    body += Pos(back_wall + channel + lip_wall / 2, length / 2, lip_top / 2) * Box(
        lip_wall, length, lip_top
    )

    # Teardrop screw bore: the round hole plus a 45-degree roof, so the
    # horizontal bore prints without sagging.
    r = screw_hole / 2
    a = r / sqrt(2)
    tear = Circle(r) + Polygon((-a, a), (a, a), (0, r * sqrt(2)), align=None)
    bore = extrude(
        Plane.YZ.offset(-1) * Pos(length / 2, screw_z) * tear, amount=back_wall + 2
    )
    solid = body - bore

    if draft:
        return solid

    # Keep sharp: back face (sits on the wall), bed face, concave junctions,
    # and the bore rim the screw head seats against. Polish the rest.
    concave = [e.center() for e in concave_edges(solid)]

    def keep(e):
        bb = e.bounding_box()
        if bb.max.X < 1e-6:
            return False
        if bb.max.Z < 1e-6:
            return False
        c = e.center()
        if any((c - p).length < 1e-6 for p in concave):
            return False
        if bb.min.Z > top - 1e-6 and bb.max.Y - bb.min.Y < 1e-6:
            # Short end edges of the plate top: chamfering them makes a third
            # chamfer meet the top-front and corner ones, leaving sliver triangles.
            return False
        if abs(bb.min.Z - floor_wall) < 1e-6 and abs(bb.max.Z - floor_wall) < 1e-6:
            # Channel floor: the bundle rests here, and an end chamfer thins
            # the 2.0 floor below what the printer lays down reliably.
            return False
        near_bore = sqrt((c.Y - length / 2) ** 2 + (c.Z - screw_z) ** 2)
        if bb.max.X < back_wall + 1e-6 and near_bore < 4.0:
            return False
        return True

    return polish(solid, solid.edges().filter_by(keep), 1.0)
