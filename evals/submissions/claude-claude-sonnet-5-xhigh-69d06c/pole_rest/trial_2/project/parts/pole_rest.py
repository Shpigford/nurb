from nurb import *

# Fixed by the bench interface: several rests stand in a row and the pole
# lies across all of them at this height, centered in X over each footprint.
AXIS_HEIGHT = 18.0

# How far the seat sits outside the pole's own radius. Close enough that the
# seat surface backs the pole (support check) while staying clear of it (fit
# check); not a user choice, it is the geometry of the joint.
SEAT_CLEARANCE = 0.25


@part
def pole_rest(pole_diameter=20.0, length=25.0, seat_thickness=3.0, draft=False):
    """
    pole_diameter: diameter of the pole this rest cradles
    length: how far the rest runs along the pole
    seat_thickness: material thickness behind the pole's seat
    """
    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + SEAT_CLEARANCE
    bottom_thickness = AXIS_HEIGHT - seat_radius

    if pole_diameter <= 0:
        reject(f"pole_diameter {pole_diameter} must be positive", param="pole_diameter")
    if length < 20.0:
        reject(f"length {length} is under the 20mm the rest needs to hold the pole: raise it to at least 20.0", param="length")
    if seat_thickness < 1.5:
        reject(f"seat_thickness {seat_thickness} is under the 1.5mm this cradle needs behind the pole's surface: raise it above 1.5", param="seat_thickness")
    if bottom_thickness < 1.5:
        reject(
            f"pole_diameter {pole_diameter} sinks the seat to within {bottom_thickness:.2f}mm of the bed at the fixed 18mm axis height: lower pole_diameter below {2 * (AXIS_HEIGHT - 1.5 - SEAT_CLEARANCE):.1f}",
            param="pole_diameter",
        )

    half_width = seat_radius + seat_thickness

    block = Pos(0, 0, AXIS_HEIGHT / 2) * Box(2 * half_width, length, AXIS_HEIGHT)
    seat_cut = Pos(0, 0, AXIS_HEIGHT) * Rot(-90, 0, 0) * Cylinder(seat_radius, length + 10)
    body = block - seat_cut

    if draft:
        return body

    bed = body.bounding_box().min.Z

    def lies_flat(axis_min, axis_max, value):
        return abs(axis_min - value) < 1e-6 and abs(axis_max - value) < 1e-6

    def on_seat(e):
        mid = e.position_at(0.5)
        dist = ((mid.X**2) + (mid.Z - AXIS_HEIGHT) ** 2) ** 0.5
        return abs(dist - seat_radius) < 1e-6

    concave = concave_edges(body)
    keep = body.edges().filter_by(
        lambda e: e not in concave
        and not lies_flat(e.bounding_box().min.Z, e.bounding_box().max.Z, bed)
        # the seat surface's rim, mouth line and end arcs alike: fit-critical,
        # never touched even though it reads as an ordinary convex edge
        and not on_seat(e)
        # the short shelf-end edges at each top-outer corner: dropping these
        # keeps three 1mm chamfers from mitering into a corner sliver there
        and not (
            lies_flat(e.bounding_box().min.Z, e.bounding_box().max.Z, AXIS_HEIGHT)
            and lies_flat(abs(e.bounding_box().min.Y), abs(e.bounding_box().max.Y), length / 2)
        )
    )
    return polish(body, keep, 1.0)
