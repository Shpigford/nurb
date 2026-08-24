from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall clip for a horizontal cable bundle, one M4 pan-head screw.

    bundle_diameter: width of the taped cable bundle the clip holds
    """
    if bundle_diameter < 4.0:
        reject(
            "bundle_diameter 4.0 mm is the smallest this clip can hold",
            param="bundle_diameter",
        )

    # 0.4 mm is the fit minimum; a hair more keeps the test cylinder free
    # of the walls instead of tangent.
    clearance = 0.5
    inner = bundle_diameter + clearance
    inner_r = inner / 2.0

    length = 14.0
    wall = 2.4
    plate = 3.0
    plate_gap = 0.4
    hole_d = 4.4
    hole_r = hole_d / 2.0
    head_clear_r = 8.4 / 2.0
    screw_gap = 1.0

    x_c = plate + plate_gap + inner_r
    z_c = wall + inner_r
    x_front_inner = x_c + inner_r
    x_front_outer = x_front_inner + wall

    bundle_top = z_c + bundle_diameter / 2.0
    z_s = bundle_top + screw_gap + head_clear_r
    plate_top = z_s + hole_r + wall
    head_bottom = z_s - head_clear_r

    # Lip reaches past the bundle centre so a 1 mm +X nudge hits solid
    # wall, but stays below the 8.4 mm driver cylinder.
    lip_top = min(z_c + inner_r * 0.5, head_bottom - 1.0)
    min_lip = z_c - bundle_diameter / 2.0 + 1.6
    if lip_top < min_lip:
        extra = min_lip - lip_top
        z_s += extra
        plate_top += extra
        head_bottom += extra
        lip_top = min_lip

    y_s = length / 2.0

    back = Box(plate, length, plate_top, align=(Align.MIN, Align.MIN, Align.MIN))
    base = Box(x_front_outer, length, wall, align=(Align.MIN, Align.MIN, Align.MIN))
    front = Box(wall, length, lip_top, align=(Align.MIN, Align.MIN, Align.MIN))
    front = Pos(x_front_inner, 0, 0) * front
    body = back + base + front

    bore = Pos(plate / 2.0, y_s, z_s) * Rot(0, 90, 0) * Cylinder(hole_r, plate + 2.0)
    body = body - bore

    if draft:
        return body

    # Chamfer only long Y-running edges below the back-plate roof. A 1 mm
    # bevel on the 3 mm plate's top corners, or on the hole rims, leaves
    # slivers or eats the 2.4 mm seating length.
    bed = body.bounding_box().min.Z
    concave = set(concave_edges(body))
    circles = set(body.edges().filter_by(GeomType.CIRCLE))
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 0.05
        and e.bounding_box().max.Z < plate_top - 0.2
        and (e.bounding_box().max.Y - e.bounding_box().min.Y) > 8.0
        and e not in concave
        and e not in circles
    )
    return polish(body, keep, 1.0)
