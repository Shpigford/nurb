from nurb import *

# The pole lies across a row of identical rests, so the interface is fixed by the
# bench and not by this part: axis along Y, exactly this high, centered in X.
POLE_AXIS_HEIGHT = 18.0


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    finish_clearance=0.25,
    cradle_wall=3.0,
    rest_length=22.0,
    foot_taper=4.25,
    chamfer_size=1.0,
    draft=False,
):
    """A cradle that holds a freshly finished pole while it dries.

    pole_diameter: how thick the pole is across
    finish_clearance: gap between the soft finish and the cradle, all the way round
    cradle_wall: how much material sits behind the cradle surface
    rest_length: how far the rest runs along the pole
    foot_taper: how far the sides pull in at 45 degrees toward the bed
    chamfer_size: size of the chamfer on the exposed edges
    """
    cradle_radius = pole_diameter / 2 + finish_clearance
    floor = POLE_AXIS_HEIGHT - cradle_radius

    if floor < cradle_wall:
        reject(
            f"a {pole_diameter}mm pole seats {floor:.2f} above the bed at the fixed "
            f"{POLE_AXIS_HEIGHT}mm axis height, which leaves less than the "
            f"{cradle_wall}mm cradle wall underneath: keep pole_diameter under "
            f"{2 * (POLE_AXIS_HEIGHT - cradle_wall - finish_clearance):.1f}",
            param="pole_diameter",
        )

    half_width = cradle_radius + cradle_wall
    taper = min(foot_taper, half_width - cradle_radius / 2, POLE_AXIS_HEIGHT / 3)

    # Cross-section in XZ, extruded along the pole. The sides rise vertically to the
    # rim and pull in at 45 degrees for the last few millimetres, so the whole outline
    # prints without support and the foot is narrower than the shoulders.
    outline = [
        (-half_width + taper, 0.0),
        (half_width - taper, 0.0),
        (half_width, taper),
        (half_width, POLE_AXIS_HEIGHT),
        (-half_width, POLE_AXIS_HEIGHT),
        (-half_width, taper),
    ]
    body = extrude(
        Plane.XZ * Polygon(*outline, align=None),
        amount=rest_length / 2,
        both=True,
    )

    # A true half-cylinder: the seat is exactly the lower half of the pole, so the
    # pole drops straight in from above and is carried on 180 degrees of contact.
    seat = (
        Pos(0, 0, POLE_AXIS_HEIGHT)
        * Rot(90, 0, 0)
        * Cylinder(cradle_radius, rest_length + 4)
    )
    body = body - seat

    if draft:
        return body

    def on_seat(edge):
        pts = [v.to_tuple() for v in edge.vertices()] + [edge.center().to_tuple()]
        return all(
            abs((p[0] ** 2 + (p[2] - POLE_AXIS_HEIGHT) ** 2) ** 0.5 - cradle_radius)
            < 0.05
            for p in pts
        )

    def rim_end(edge):
        # The short cross-wise edges closing each end of the rim. Chamfering them
        # would put three chamfers into one corner and leave a sliver facet there.
        bb = edge.bounding_box()
        return bb.min.Z > POLE_AXIS_HEIGHT - 0.01 and bb.size.X > 0.01

    concave = set(concave_edges(body))
    keep = body.edges().filter_by(
        lambda e: e not in concave
        and e.bounding_box().min.Z > 0.01
        and not on_seat(e)
        and not rim_end(e)
    )
    return polish(body, keep, chamfer_size)
