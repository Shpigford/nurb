from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip that holds a taped cable bundle with one M4 pan-head screw.

    bundle_diameter: caliper width of the cable bundle the clip holds
    """
    if bundle_diameter < 4.0:
        reject(
            "bundle_diameter is under 4mm; raise it so the clip can wrap the bundle",
            param="bundle_diameter",
        )

    length = 12.0
    clearance = 0.4
    fit = bundle_diameter + clearance
    back = 3.2
    floor = 2.4
    lip = 2.4
    lip_above_center = 3.6
    hole_dia = 4.4
    hole_r = hole_dia / 2.0
    head_r = 8.4 / 2.0
    around = 2.4

    pocket_x = back + fit
    outer_x = pocket_x + lip
    center_z = floor + fit / 2.0
    lip_top = center_z + lip_above_center
    screw_z = lip_top + head_r + around
    tab_top = screw_z + hole_r + around

    with BuildSketch(Plane.XZ) as profile:
        Polygon(
            (0.0, 0.0),
            (outer_x, 0.0),
            (outer_x, lip_top),
            (pocket_x, lip_top),
            (pocket_x, floor),
            (back, floor),
            (back, tab_top),
            (0.0, tab_top),
        )
    body = extrude(profile.sketch, amount=length, dir=(0, 1, 0))

    hole = Pos(back / 2.0, length / 2.0, screw_z) * Rot(0, 90, 0) * Cylinder(
        hole_r, back + 2.0
    )
    body -= hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    wall = body.bounding_box().min.X
    inside = concave_edges(body)
    keep = body.edges().filter_by(Axis.Y).filter_by(
        lambda e: e.bounding_box().min.Z > bed + 0.05
        and e.bounding_box().min.X > wall + 0.05
        and abs(e.center().X - pocket_x) > 0.2
        and e not in inside
    )
    return polish(body, keep, 1.0)
