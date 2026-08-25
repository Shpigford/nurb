import math

from nurb import *


AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=20.0,
    cradle_length=24.0,
    wall_thickness=3.0,
    pole_clearance=0.2,
    wrap_angle=140.0,
    draft=False,
):
    """A support-free cradle for a finished pole lying across a row of rests.

    pole_diameter: diameter of the pole being dried
    cradle_length: length of the rest along the pole's Y axis
    wall_thickness: material backing the pole's cradle surface
    pole_clearance: radial gap protecting the soft finish
    wrap_angle: continuous supported arc around the pole
    """
    if pole_diameter <= 0.0:
        reject("pole_diameter must be positive", param="pole_diameter")
    if pole_clearance < 0.1:
        reject("pole_clearance must be at least 0.1 mm", param="pole_clearance")
    if wrap_angle < 120.0 or wrap_angle >= 180.0:
        reject("wrap_angle must be from 120 up to, but not including, 180 degrees", param="wrap_angle")

    radius = pole_diameter / 2.0 + pole_clearance
    if radius >= AXIS_HEIGHT:
        reject("pole_diameter and pole_clearance put the seat through the bed", param="pole_diameter")

    half_angle = math.radians(wrap_angle / 2.0)
    opening_half_width = radius * math.sin(half_angle)
    width = 2.0 * (opening_half_width + wall_thickness)
    top_z = AXIS_HEIGHT - radius * math.cos(half_angle)

    # A box with a cylinder removed makes a constant, continuous cradle along Y.
    # Its top is below the pole axis, leaving a straight vertical drop path.
    body = Box(width, cradle_length, top_z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cutter = Cylinder(
        radius,
        cradle_length + 2.0,
        rotation=(90, 0, 0),
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).translate((0, 0, AXIS_HEIGHT))
    body = body - cutter

    if draft:
        return body

    # The cylindrical seat and bed edges are fit-critical / non-cosmetic.
    # Chamfer only exposed non-bed, non-seat edges.
    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    seat_edges = [
        edge
        for face in body.faces()
        if face.geom_type == GeomType.CYLINDER
        for edge in face.edges()
    ]
    exposed = body.edges().filter_by(
        lambda edge: edge.bounding_box().min.Z > bed + 1e-6
        and edge not in concave
        and edge not in seat_edges
    )
    return polish(body, exposed, 1.0)
