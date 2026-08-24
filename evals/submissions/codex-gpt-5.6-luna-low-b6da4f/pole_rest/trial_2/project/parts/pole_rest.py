from nurb import *
import math


@part
def pole_rest(pole_diameter=20.0, length=24.0, foot_width=24.0,
              foot_depth=24.0, cradle_wall=2.0, clearance=0.1,
              draft=False):
    """Rest for a drying pole.

    pole_diameter: diameter of the finished pole
    length: length of the cradle along the pole
    foot_width: width of the stable bench footprint
    foot_depth: front-to-back depth of the footprint
    cradle_wall: radial material thickness behind the cradle
    clearance: air gap between pole and cradle
    """
    radius = pole_diameter / 2.0
    inner = radius + clearance
    outer = inner + cradle_wall
    axis_z = 18.0

    # A sampled annular sector, 120 degrees centered beneath the pole.  The
    # sector is extruded along Y, leaving the top open for a vertical drop-in.
    outer_pts = []
    inner_pts = []
    for i in range(13):
        angle = math.radians(210.0 + 120.0 * i / 12.0)
        outer_pts.append((outer * math.cos(angle), axis_z + outer * math.sin(angle)))
    for i in range(12, -1, -1):
        angle = math.radians(210.0 + 120.0 * i / 12.0)
        inner_pts.append((inner * math.cos(angle), axis_z + inner * math.sin(angle)))

    arc = extrude(Plane.XZ * make_face(Polygon(*(outer_pts + inner_pts))),
                  amount=length)
    arc = Pos(0, length / 2.0, 0) * arc
    foot = Pos(0, 0, 6.0) * Box(foot_width, foot_depth, 12.0)
    body = foot + arc
    if draft:
        return body
    return body
