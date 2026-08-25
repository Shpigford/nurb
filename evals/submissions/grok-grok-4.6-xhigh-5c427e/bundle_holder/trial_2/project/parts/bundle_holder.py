from nurb import *


@part
def bundle_holder(bundle_diameter=measured("bundle_diameter"), draft=False):
    """Wall-mounted clip that traps a horizontal cable bundle with one M4 pan-head screw.

    bundle_diameter: width of the taped cable bundle the clip holds
    """
    if bundle_diameter < 4.0:
        reject(
            f"bundle_diameter {bundle_diameter} is under 4mm: raise it so the seat can print",
            param="bundle_diameter",
        )

    # Seat is 0.4 larger than the bundle so an 8.0 cylinder fits with 8.4 across.
    cavity = bundle_diameter + 0.4
    wall = 2.2
    floor = 2.2
    roof = 2.2
    plate = 3.0
    length = 10.0
    hole_d = 4.4
    head_d = 8.4
    around = 3.2
    driver_gap = 0.8

    depth = plate + cavity + wall
    tunnel_h = floor + cavity + roof
    screw_z = tunnel_h + driver_gap + head_d / 2
    plate_top = screw_z + hole_d / 2 + around

    # Side profile in XZ: thick tunnel body plus a tall back plate for the screw.
    wire = Plane.XZ * Polyline(
        (0, 0),
        (depth, 0),
        (depth, tunnel_h),
        (plate, tunnel_h),
        (plate, plate_top),
        (0, plate_top),
        (0, 0),
    )
    body = extrude(make_face(wire), amount=length)
    body = Pos(0, length / 2, 0) * body

    tunnel = (
        Pos(plate + cavity / 2, 0, floor + cavity / 2)
        * Rot(90, 0, 0)
        * Cylinder(cavity / 2, length + 2, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    )
    body = body - tunnel

    hole = (
        Pos(-1, 0, screw_z)
        * Rot(0, 90, 0)
        * Cylinder(hole_d / 2, plate + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    body = body - hole

    if draft:
        return body

    bed = body.bounding_box().min.Z
    xmin = body.bounding_box().min.X
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-4 and e.bounding_box().min.X > xmin + 1e-4
    )
    keep = keep - concave_edges(body)
    keep = keep.filter_by(lambda e: e.geom_type != GeomType.CIRCLE)
    return polish(body, keep, 1.0)
