from nurb import *

# Fixed by the bench interface: every rest in the row holds the pole's
# axis at this height, whatever pole_diameter the rest is built for.
AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    width=28.0,
    length=22.0,
    side_wall=3.5,
    seat_clearance=0.3,
    draft=False,
):
    """
    pole_diameter: the diameter of the pole this rest cradles
    width: how wide the rest is across the bench, side to side
    length: how far the rest runs along the pole
    side_wall: material left beside the seat on each side
    seat_clearance: gap between the seat and the pole's surface
    """
    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + seat_clearance

    if seat_radius >= AXIS_HEIGHT:
        reject(
            f"pole_diameter {pole_diameter} gives a seat radius of "
            f"{seat_radius:.2f}mm, past the fixed {AXIS_HEIGHT}mm axis height: "
            f"the seat would dig into the bed. Lower pole_diameter.",
            param="pole_diameter",
        )

    min_width = 2 * (seat_radius + 2.0)
    if width < min_width:
        reject(
            f"width {width} leaves under 2mm beside the {seat_radius:.2f}mm seat: "
            f"raise width above {min_width:.1f}",
            param="width",
        )

    block = Box(
        width, length, AXIS_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    seat = Pos(0, 0, AXIS_HEIGHT) * Rot(-90, 0, 0) * Cylinder(
        seat_radius, length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    body = block - seat

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    seat_faces = body.faces().filter_by(GeomType.CYLINDER)
    seat_edges = seat_faces.edges()
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
    )
    keep = keep.filter_by(lambda e: e not in concave and e not in seat_edges)
    return polish(body, keep, 1.0)
