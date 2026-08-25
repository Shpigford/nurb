from nurb import *

# Pole axis is a bench constraint: rests in a row, pole along Y, axis 18mm up.
AXIS_HEIGHT = 18.0
# Soft finish: cradle the round, never perch it on edges. 0.2 sits between
# the 0.1mm keep-off and the 0.4mm contact band.
CLEARANCE = 0.20
WALL = 3.0
# Full-length cradle; longer than the 20mm minimum so end chamfers cannot
# eat the 120 degree support arc.
REST_LENGTH = 24.0


@part
def pole_rest(pole_diameter=measured("pole_diameter"), draft=False):
    """Rest that cradles a freshly finished pole while the finish dries.

    pole_diameter: width of the pole this rest holds
    """
    radius = pole_diameter / 2.0
    inner = radius + CLEARANCE
    floor = AXIS_HEIGHT - inner
    if inner <= 1.0:
        reject(
            f"pole_diameter {pole_diameter} is too small to cut a drop-in cradle "
            f"under the {AXIS_HEIGHT}mm axis",
            param="pole_diameter",
        )
    if floor < WALL:
        reject(
            f"pole_diameter {pole_diameter} leaves only {floor:.1f}mm of floor "
            f"under the {AXIS_HEIGHT}mm axis; keep it under "
            f"{2.0 * (AXIS_HEIGHT - WALL - CLEARANCE):.1f}",
            param="pole_diameter",
        )

    half = inner + WALL
    top = AXIS_HEIGHT

    with BuildPart() as rest:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Polyline((-half, 0), (half, 0), (half, top), (inner, top))
                ThreePointArc((inner, top), (0, top - inner), (-inner, top))
                Polyline((-inner, top), (-half, top), (-half, 0))
            make_face()
        extrude(amount=REST_LENGTH / 2.0, both=True)

    body = rest.part
    if draft:
        return body

    bed = body.bounding_box().min.Z
    cradle = body.faces().filter_by(GeomType.CYLINDER)
    keep = body.edges().filter_by(lambda e: e.bounding_box().min.Z > bed + 1e-4)
    keep = keep - concave_edges(body) - cradle.edges()
    return polish(body, keep, 1.0)
