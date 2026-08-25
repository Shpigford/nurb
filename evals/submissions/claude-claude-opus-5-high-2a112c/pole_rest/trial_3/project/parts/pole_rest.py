from nurb import *

# Every rest in the row hands the pole to the next one, so the seat height is an
# interface, not a preference: the axis sits exactly this far above the bench.
POLE_AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    rest_length=22.0,
    seat_clearance=0.25,
    wall_thickness=3.0,
    chamfer_size=1.0,
    draft=False,
):
    """A cradle that holds a freshly finished pole off the bench while it dries.

    pole_diameter: how thick the pole is across, measured with calipers
    rest_length: how far the rest runs along the pole
    seat_clearance: the gap between the seat and the finish, so nothing rubs
    wall_thickness: how much material stands beside the seat at the rim
    chamfer_size: how big the bevel on the handled edges is
    """
    pole_radius = pole_diameter / 2.0
    seat_radius = pole_radius + seat_clearance
    floor = POLE_AXIS_HEIGHT - seat_radius
    if floor < 2.5:
        reject(
            "a pole this thick would have its seat cut through the bench-side floor "
            f"at the fixed {POLE_AXIS_HEIGHT}mm axis height",
            "pole_diameter",
        )
    half_width = seat_radius + wall_thickness

    body = Pos(0, 0, POLE_AXIS_HEIGHT / 2) * Box(
        2 * half_width, rest_length, POLE_AXIS_HEIGHT
    )
    # The seat is the pole's own circle plus the clearance, cut from the top face:
    # its widest point lands exactly at the axis, so the pole drops straight in and
    # the cradle wraps it well past the 120 degrees that stops it rocking.
    seat = (
        Pos(0, 0, POLE_AXIS_HEIGHT)
        * Rot(90, 0, 0)
        * Cylinder(seat_radius, rest_length + 2)
    )
    body = body - seat

    if draft:
        return body

    bed = body.bounding_box().min.Z
    concave = concave_edges(body)
    # The seat's two end circles stay sharp: chamfering a circle raises a cone that
    # collides with the rim chamfer beside it and leaves four sliver facets.
    keep = body.edges().filter_by(
        lambda e: e.bounding_box().min.Z > bed + 1e-6
        and e not in concave
        and e.geom_type == GeomType.LINE
    )
    return polish(body, keep, chamfer_size)
