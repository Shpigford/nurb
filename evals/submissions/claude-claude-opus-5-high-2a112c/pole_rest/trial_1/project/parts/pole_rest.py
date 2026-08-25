from nurb import *


@part
def pole_rest(
    pole_diameter=measured("pole_diameter"),
    pole_height=18.0,
    pole_clearance=0.3,
    cradle_wall=3.0,
    rest_length=22.0,
    foot_setback=4.0,
    foot_height=6.0,
    chamfer_size=1.2,
    draft=False,
):
    """A drying rest: the pole lies in the cradle, several rests in a row.

    pole_diameter: how thick the pole is
    pole_height: how high the pole's centre sits above the bench
    pole_clearance: the gap left between the pole's finish and the cradle
    cradle_wall: how much material wraps around the outside of the cradle
    rest_length: how far the rest reaches along the pole
    foot_setback: how much narrower the foot is than the shoulders
    foot_height: how tall the straight part of the foot is
    chamfer_size: the facet taken off every exposed edge
    """
    seat_radius = pole_diameter / 2.0 + pole_clearance
    shoulder_half = seat_radius + cradle_wall
    foot_half = shoulder_half - foot_setback
    shoulder_z = foot_height + foot_setback  # the flare is a 45 degree facet

    floor = pole_height - seat_radius
    if floor < 3.0:
        reject(
            f"a {pole_diameter}mm pole seated at {pole_height} leaves only "
            f"{floor:.1f}mm of floor under the cradle: raise pole_height above "
            f"{seat_radius + 3.0:.1f}",
            param="pole_height",
        )
    if foot_half < 3.0:
        reject(
            f"foot_setback {foot_setback} leaves a {2 * foot_half:.1f}mm foot: "
            f"lower it below {shoulder_half - 3.0:.1f}",
            param="foot_setback",
        )
    if shoulder_z > pole_height - 2.0:
        reject(
            f"the flare tops out at {shoulder_z:.1f}, into the {pole_height} rim: "
            f"lower foot_height below {pole_height - 2.0 - foot_setback:.1f}",
            param="foot_height",
        )

    # Profile in XZ: a foot, a 45 degree flare, then shoulders up to the pole's axis.
    outline = [
        (-foot_half, 0.0),
        (foot_half, 0.0),
        (foot_half, foot_height),
        (shoulder_half, shoulder_z),
        (shoulder_half, pole_height),
        (-shoulder_half, pole_height),
        (-shoulder_half, shoulder_z),
        (-foot_half, foot_height),
    ]
    block = extrude(
        Plane.XZ * Polygon(*outline, align=None),
        amount=rest_length / 2.0,
        both=True,
    )

    # The block stops at the axis, so cutting the whole pole leaves a 180 degree seat
    # and nothing overhanging the drop-in path.
    seat = (
        Pos(0, 0, pole_height)
        * Rotation(90, 0, 0)
        * Cylinder(seat_radius, rest_length + 2.0)
    )
    body = block - seat

    if draft:
        return body

    # Sharp: the bed-contact face, the concave root of the flare, and the whole seat,
    # which is mating geometry and gets no lead-in.
    bed = body.bounding_box().min.Z
    sharp = set()
    for face in body.faces().filter_by(GeomType.CYLINDER):
        sharp.update(_key(e) for e in face.edges())
    sharp.update(_key(e) for e in concave_edges(body))
    keep = [
        e
        for e in body.edges()
        if e.bounding_box().max.Z > bed + 1e-6 and _key(e) not in sharp
    ]
    return polish(body, keep, chamfer_size)


def _key(edge):
    c = edge.center()
    return tuple(round(v, 4) for v in (c.X, c.Y, c.Z, edge.length))
